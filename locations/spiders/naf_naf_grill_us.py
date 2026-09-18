import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# Narrow/non-breaking spaces and various dash characters the site uses
# inconsistently between locations.
WHITESPACE_AND_DASHES = str.maketrans({"\xa0": " ", " ": " ", " ": " ", "–": "-", "—": "-"})


def _parse_12h_time(value: str) -> str:
    hour, minute, meridiem = re.match(r"(\d{1,2})(?::(\d{2}))?\s*([AaPp][Mm])", value.strip()).groups()
    hour, minute = int(hour), int(minute or 0)
    if meridiem.lower() == "pm" and hour != 12:
        hour += 12
    elif meridiem.lower() == "am" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


class NafNafGrillUSSpider(Spider):
    name = "naf_naf_grill_us"
    item_attributes = {"brand": "Naf Naf Grill", "brand_wikidata": "Q111901442", "name": "Naf Naf Grill"}
    start_urls = ["https://www.nafnafgrill.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//h3[contains(text(), "Naf Naf Grill")]/..'):
            item = Feature()
            branch = location.xpath("h3/text()").get().removeprefix("Naf Naf Grill ")
            item["branch"] = re.sub(r"\s*\([^)]*\)\s*$", "", branch).strip()
            item["ref"] = re.sub(r"[^a-z0-9]+", "-", item["branch"].lower()).strip("-")

            addr_full = "".join(location.xpath("p[1]//text()").getall()).translate(WHITESPACE_AND_DASHES)
            addr_full = re.sub(r"\s+", " ", addr_full).strip()
            item["addr_full"] = addr_full
            if m := re.search(r"\b([A-Z]{2})\s+(\d{5})\b", addr_full):
                item["state"], item["postcode"] = m.groups()

            item["phone"] = location.xpath('p[strong[contains(., "Phone")]]/text()').get()

            oh = OpeningHours()
            for day_row in location.xpath("ul/li"):
                day = day_row.xpath('span[@class="label"]/text()').get()
                hours = day_row.xpath('span[@class="value"]/text()').get("").translate(WHITESPACE_AND_DASHES).strip()
                if not day or not hours:
                    continue
                if hours.lower() == "closed":
                    oh.add_range(day, "closed", "closed")
                else:
                    open_time, close_time = re.split(r"\s*-\s*", hours, maxsplit=1)
                    oh.add_range(day, _parse_12h_time(open_time), _parse_12h_time(close_time))
            item["opening_hours"] = oh

            item["website"] = "https://www.nafnafgrill.com/locations/#{}".format(location.xpath("h3/@id").get())

            apply_category(Categories.RESTAURANT, item)

            yield item
