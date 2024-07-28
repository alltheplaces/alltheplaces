import chompjs
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BravoItalianUSSpider(Spider):
    name = "bravo_italian_us"
    item_attributes = {"brand": "Bravo Cucina", "brand_wikidata": "Q64055574"}
    allowed_domains = ["www.bravoitalian.com"]
    start_urls = ["https://www.bravoitalian.com/locations/"]

    def parse(self, response):
        feature_collection = (
            response.xpath("//script[contains(text(), 'FeatureCollection')]/text()")
            .get()
            .split(" const geoObject = ")[1]
        )
        for location in chompjs.parse_js_object(feature_collection)["features"]:
            item = DictParser().parse(location["properties"])
            item["ref"] = location["properties"]["api_id"]
            item["geometry"] = location["geometry"]
            item["opening_hours"] = OpeningHours()
            for hours in location["properties"]["more_hours"]:
                if hours["is_closed"] is False:
                    item["opening_hours"].add_range(hours["open_day"], hours["open_time"], hours["close_time"])

            yield item
