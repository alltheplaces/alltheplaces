import chompjs
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SizzlerSpider(Spider):
    name = "sizzler"
    item_attributes = {"brand": "Sizzler", "brand_wikidata": "Q1848822"}
    allowed_domains = ["sizzler.com"]
    start_urls = ["https://sizzler.com/locations/"]

    def parse(self, response):
        locations_raw = (
            response.xpath('//script[contains(text(), "var locations_meta = ")]/text()')
            .get()
            .split("var locations_meta = ", 1)[1]
            .split("var locationsMapObject = ", 1)[0]
        )
        for location in chompjs.parse_js_object(locations_raw):
            location = location["location"]
            item = DictParser.parse(location)
            item["ref"] = location["branch_id"]
            item["name"] = location["branch_name"].split("|", 1)[0]
            item["lat"] = float(location["map_pin"].get("lat"))
            item["lon"] = float(location["map_pin"].get("lng"))
            item["housenumber"] = location["map_pin"].get("street_number")
            item["street"] = location["map_pin"].get("street_name")
            item["city"] = location["map_pin"].get("city")
            item["state"] = location["map_pin"].get("state")
            item["postcode"] = location["map_pin"].get("post_code")
            item["street_address"] = location["map_pin"].get("address")
            item["phone"] = location["store_phone_number"]
            item["website"] = "https://sizzler.com/locations/sizzler-" + item["city"].lower().replace(" ", "-") + "/"
            item["opening_hours"] = OpeningHours()
            for day_name, hours_range in location["opening_hours"].items():
                item["opening_hours"].add_range(
                    day_name.title(),
                    hours_range.split(" - ", 1)[0].upper(),
                    hours_range.split(" - ", 1)[1].upper(),
                    "%I:%M%p",
                )
            yield item
