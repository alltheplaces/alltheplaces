import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_BG, OpeningHours, sanitise_day
from locations.items import Feature


class ZoraBGSpider(SitemapSpider):
    name = "zora_bg"
    item_attributes = {
        "brand": "Зора",
        "brand_wikidata": "Q111648360",
        "country": "BG",
    }
    sitemap_urls = ["https://zora.bg/sitemap/page/1.xml"]
    sitemap_rules = [("/page/store-", "parse_stores"), ("/page/stores-", "parse_stores")]

    no_refs = True

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        stores = response.xpath("//iframe[@allowfullscreen]")
        coords_pattern = re.compile(r"(\d+\.\d+),\s*(\d+\.\d+)")
        opening_hours_pattern = re.compile(r"([а-я]+)-?([а-я]+)?\s*:\s*([\d:]+-[\d:]+|почивен)")

        for store in stores:
            item = Feature()

            columns = store.xpath(".//../../following-sibling::div")
            middle_section = columns[0].xpath(".//text()").getall()
            middle_section_text = [row.replace("\n", "").strip() for row in middle_section]
            middle_section_text = [row for row in middle_section_text if row and not row.startswith("<!--")]

            phone = next((row for row in middle_section_text if row.startswith("+359")), None)
            item["phone"] = phone

            phone_index = middle_section_text.index(phone) if phone else -1
            if phone_index > 3:
                # Addresses are sometimes split into multiple html elements
                item["street_address"] = " ".join(middle_section_text[1 : phone_index - 1])
            else:
                item["street_address"] = middle_section_text[1]

            coords = coords_pattern.match(middle_section_text[-1])
            if coords:
                # Coordinates are not always present...
                lat, lon = coords.groups()
                item["lat"] = lat
                item["lon"] = lon

            last_section = columns[1]  # contains opening hours
            last_section_text = last_section.xpath(".//text()").getall()
            last_section_text = [row.replace("\n", "").strip().lower() for row in last_section_text]
            last_section_text = [row for row in last_section_text if row]
            first_index = next((i for i, row in enumerate(last_section_text) if row.startswith("понеделник")), None)
            if first_index is not None:
                # it is already quite bad, might as well
                # merge everything into one string and
                # parse it with regex
                opening_hours_raw = " ".join(last_section_text[first_index : first_index + 10])
                opening_hours_raw = (
                    opening_hours_raw.replace("ч.", "")
                    .replace(" - ", "-")
                    .replace("- ", "-")
                    .replace("ден", "")
                    .replace(" :", ":")
                    .strip()
                )
                groups = opening_hours_pattern.findall(opening_hours_raw)

                opening_hours = OpeningHours()
                for group in groups:
                    [day1, day2, hours] = group
                    if day1 and day2:
                        days_range = opening_hours.days_in_day_range([day1, day2], DAYS_BG)
                        if hours == "почивен":
                            opening_hours.set_closed(days_range)
                        else:
                            [start_time, end_time] = hours.split("-")
                            opening_hours.add_days_range(days_range, start_time, end_time)
                    elif day1:
                        day = sanitise_day(day1, DAYS_BG)
                        if hours == "почивен":
                            opening_hours.set_closed(day)
                        else:
                            [start_time, end_time] = hours.split("-")
                            opening_hours.add_range(day, start_time, end_time)
                item["opening_hours"] = opening_hours.as_opening_hours()
            yield item
