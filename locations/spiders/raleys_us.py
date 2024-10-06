from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

BRAND_WIKIDATA = {
    "Bel Air": "Q112922067",
    "Nob Hill Foods": "Q121816894",
    "Raley's": "Q7286970",
    "Raley's ONE Market": "Q7286970",
}


class RaleysUSSpider(Spider):
    name = "raleys_us"
    item_attributes = {"extras": Categories.SHOP_SUPERMARKET.value}
    custom_settings = {"DOWNLOAD_TIMEOUT": 55}

    def start_requests(self):
        yield JsonRequest(
            "https://www.raleys.com/api/store", data={"rows": 250, "searchParameter": {"shippingMethod": "pickup"}}
        )

    def parse(self, response):
        result = response.json()

        if result["limit"] < result["total"]:
            raise RuntimeError(f"Got {result['total']} results, need to increase limit")

        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location["number"]
            item["website"] = f"https://www.raleys.com/store/{location['number']}"
            item["brand"] = item["name"] = location["brand"]["name"]
            item["brand_wikidata"] = BRAND_WIKIDATA[location["brand"]["name"]]
            item["street_address"] = item.pop("street")

            oh = OpeningHours()
            # TODO: Is it safe to assume that all stores are open 7 days?
            oh.add_ranges_from_string(f"Mo-Su {location['storeHours'].removeprefix('Between ')}")
            item["opening_hours"] = oh

            yield item
