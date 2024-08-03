from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class CumberlandFarmsUSSpider(Spider):
    name = "cumberland_farms_us"
    item_attributes = {"brand": "Cumberland Farms", "brand_wikidata": "Q1143685"}
    allowed_domains = ["cumberlandfarms.com"]
    start_urls = ["https://www.cumberlandfarms.com/api/stores-locator/store-locator-search/results?bannerId=1"]

    def parse(self, response, **kwargs):
        results = response.json()["value"]["listResults"]
        for location in results["pageItems"]:
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)
            item["website"] = location["pageUrl"]

            features = [f["name"] for f in location["features"]]

            if "Fuel" in features:
                apply_category(Categories.FUEL_STATION, item)
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            apply_yes_no("sells:alcohol", item, "Beer" in features)

            yield item

        if results["pageNumber"] < results["totalPages"]:
            yield JsonRequest(
                f'https://www.cumberlandfarms.com/api/stores-locator/store-locator-search/results?bannerId=1&pageNumber={response.json()["value"]["listResults"]["pageNumber"] + 1}'
            )
