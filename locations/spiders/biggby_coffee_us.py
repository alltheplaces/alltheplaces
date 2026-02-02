
from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address

DAY_KEYS = {
    "Mo": "monday",
    "Tu": "tuesday",
    "We": "wednesday",
    "Th": "thursday",
    "Fr": "friday",
    "Sa": "sat",
    "Su": "sun",
}


class BiggbyCoffeeUSSpider(Spider):
    name = "biggby_coffee_us"
    item_attributes = {"brand": "Biggby Coffee", "brand_wikidata": "Q4906876"}
    allowed_domains = ["www.biggby.com"]
    start_urls = ["https://www.biggby.com/locations/"]

    def extract_json(self, response):
        js_blob = response.xpath('//script[contains(text(), "locations: [{")]/text()').get()
        js_blob = "[{" + js_blob.split("locations: [{", 1)[1].split("}]", 1)[0] + "}]"
        return parse_js_object(js_blob)

    def parse(self, response):
        for location in self.extract_json(response):
            meta = location.get("meta", {})
            if meta.get("store_coming_soon"):
                continue
            item = DictParser.parse(meta)
            item["street_address"] = clean_address([meta.get("address_one"), meta.get("address_two")])
            if location_map := meta.get("location_map"):
                item["addr_full"] = location_map.get("address")
                item["lat"] = location_map.get("lat")
                item["lon"] = location_map.get("lng")
            item["opening_hours"] = self.parse_hours(meta)
            apply_category(Categories.CAFE, item)
            apply_yes_no(Extras.WIFI, item, meta.get("wifi"), False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, meta.get("drive_thru"), False)
            yield item

    def parse_hours(self, meta: dict) -> OpeningHours:
        oh = OpeningHours()
        try:
            for day_abbrev, day_key in DAY_KEYS.items():
                open_hour = meta.get(f"{day_key}_open_hour")
                close_hour = meta.get(f"{day_key}_close_hour")
                if open_hour and close_hour:
                    oh.add_range(day_abbrev, open_hour, close_hour, time_format="%H%M")
        except Exception:
            pass
        return oh
