import chompjs
from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class SoulOriginAUSpider(Spider):
    name = "soul_origin_au"
    item_attributes = {"brand": "Soul Origin", "brand_wikidata": "Q110473093"}
    start_urls = ["https://www.soulorigin.com.au/pages/stores"]

    def parse(self, response):
        all_locations_text = response.xpath('//script[contains(text(), "const features = [];")]/text()').get()
        for location_text in all_locations_text.split("features.push(")[1:]:
            location = chompjs.parse_js_object(location_text)
            properties = {
                "ref": location["properties"]["articleUrl"].replace("/blogs/stores/", ""),
                "name": location["properties"]["storeName"],
                "geometry": location["geometry"],
                "addr_full": location["properties"]["address"],
                "website": "https://www.soulorigin.com.au" + location["properties"]["articleUrl"],
            }
            if "TBA" not in location["properties"]["phone"] and "NO STORE PHONE" not in location["properties"]["phone"]:
                properties["phone"] = location["properties"]["phone"]
            properties["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_name, hours_range in location["properties"]["openingHours"].items():
                hours_string = f"{hours_string} {day_name}: {hours_range}"
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
