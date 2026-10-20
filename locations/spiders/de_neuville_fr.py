import re

from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature


class DeNeuvilleFRSpider(Spider):
    name = "de_neuville_fr"
    item_attributes = {"brand": "De Neuville", "brand_wikidata": "Q106353063", "name": "De Neuville"}
    allowed_domains = ["chocolat-deneuville.com"]
    start_urls = ["https://www.chocolat-deneuville.com/magasins?ajax=1&all=1"]
    # A handful of stores are in Luxembourg, so let the reverse geocoder determine country per store
    # rather than assuming every item is in France.
    skip_auto_cc_spider_name = True

    def parse(self, response):
        for store in response.xpath("//marker"):
            item = Feature()
            item["ref"] = store.attrib.get("id_store")
            branch = re.sub(r"\s*[-–]\s*chocolat français\s*$", "", store.attrib.get("name", ""), flags=re.IGNORECASE)
            item["branch"] = branch.strip().removeprefix("De Neuville ").strip()
            item["lat"] = store.attrib.get("lat")
            item["lon"] = store.attrib.get("lng")
            item["phone"] = store.attrib.get("phone")
            item["website"] = store.attrib.get("link")

            self.parse_address(item, store.attrib.get("address", ""))

            item["opening_hours"] = self.parse_hours(store.attrib.get("other", ""))

            apply_category(Categories.SHOP_CHOCOLATE, item)

            yield item

    def parse_address(self, item: Feature, address: str):
        # Address is a series of lines separated by "<br />": one or more street/venue lines,
        # then "<city> <postcode>" (or "<postcode> <city>" for the Luxembourg stores), then phone.
        lines = [line.strip() for line in address.split("<br />") if line.strip()]
        if len(lines) < 2:
            item["addr_full"] = address
            return

        city_postcode = lines[-2]
        street_lines = lines[:-2]

        if m := re.match(r"^(.*?)\s+(\d{4,5})$", city_postcode):
            item["city"], item["postcode"] = m.group(1), m.group(2)
        elif m := re.match(r"^(\d{4,5})\s+(.*)$", city_postcode):
            item["postcode"], item["city"] = m.group(1), m.group(2)
        else:
            street_lines.append(city_postcode)

        if street_lines:
            item["street_address"] = ", ".join(street_lines)

    def parse_hours(self, other: str) -> OpeningHours:
        oh = OpeningHours()
        for p in Selector(text=other).xpath("//p"):
            day_code = DAYS_FR.get(p.xpath("string(./strong)").get("").strip().rstrip(":").strip())
            hours_text = p.xpath("string(./span)").get("").strip()
            if not day_code or not hours_text or "ferm" in hours_text.lower():
                continue
            for time_range in hours_text.split("/"):
                if "-" not in time_range:
                    continue
                open_time, close_time = (t.strip() for t in time_range.split("-", 1))
                oh.add_range(day_code, open_time, close_time, time_format="%Hh%M")
        return oh
