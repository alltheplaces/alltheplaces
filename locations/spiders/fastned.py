from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class FastnedSpider(Spider):
    name = "fastned"
    item_attributes = {"operator": "Fastned", "operator_wikidata": "Q19935749"}
    start_urls = ["https://www.fastnedcharging.com/api/v1/maplocations/"]

    def parse(self, response: Response):
        for feature in response.json()["locations"]:
            yield JsonRequest(
                url=f"https://www.fastnedcharging.com/api/v1/maplocations/{feature['id']}",
                meta={"lat": feature["coordinates"].get("latitude"), "lon": feature["coordinates"].get("longitude")},
                callback=self.parse_feature,
            )

    def parse_feature(self, response: Response):
        feature = response.json()["location"]
        item = DictParser.parse(feature)
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("addr_full")
        item["lat"] = response.meta["lat"]
        item["lon"] = response.meta["lon"]
        apply_category(Categories.CHARGING_STATION, item)
        yield item
