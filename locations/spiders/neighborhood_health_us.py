import re

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class NeighborhoodHealthUSSpider(Spider):
    name = "neighborhood_health_us"
    item_attributes = {"brand": "Neighborhood Health", "country": "US"}
    allowed_domains = ["neighborhoodhealthtn.org"]
    start_urls = ["https://neighborhoodhealthtn.org/our-locations/"]

    def parse(self, response: Response):
        for box in response.css(".elementor-widget-icon-box"):
            name = " ".join(box.css(".elementor-icon-box-title span::text").getall()).strip()
            if not name:
                continue

            address_lines = [
                line.strip() for line in box.css(".elementor-icon-box-description::text").getall() if line.strip()
            ]

            item = Feature()
            item["ref"] = name
            item["name"] = name
            item["website"] = response.url

            if address_lines:
                item["street_address"] = address_lines[0].rstrip(",").strip()
            if len(address_lines) > 1:
                if m := re.match(r"^(?P<city>.*?),?\s*TN\s*(?P<postcode>\d{5})?$", address_lines[1]):
                    item["city"] = m.group("city").strip()
                    item["state"] = "TN"
                    if m.group("postcode"):
                        item["postcode"] = m.group("postcode")

            # "Get location" buttons link to Google Maps short links (e.g. maps.app.goo.gl/...)
            # which resolve a place name server-side, so they aren't usable as a coordinate source.
            services = None
            container = box.xpath('ancestor::div[contains(concat(" ", normalize-space(@class), " "), " e-child ")]')
            if container:
                for li in container[0].css(".elementor-icon-list-text"):
                    text = re.sub(r"\s+", " ", " ".join(li.css("*::text").getall())).strip()
                    if text.startswith("Hours:"):
                        hours_text = text.removeprefix("Hours:").strip()
                        if "CLOSED" not in hours_text.upper():
                            item["opening_hours"] = OpeningHours()
                            for part in hours_text.split("*"):
                                part = re.sub(r"(?i)^also open\s*", "", part.strip())
                                if re.search(r"(?i)monday|tuesday|wednesday|thursday|friday|saturday|sunday", part):
                                    item["opening_hours"].add_ranges_from_string(part)
                    elif text.startswith("Services offered:"):
                        services = text.removeprefix("Services offered:").strip()

            if name == "Administration & Business Office" or services == "Administration":
                apply_category(Categories.OFFICE_HEALTHCARE, item)
            else:
                apply_category(Categories.CLINIC, item)

            yield item
