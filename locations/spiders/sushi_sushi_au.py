from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class SushiSushiAUSpider(Spider):
    name = "sushi_sushi_au"
    item_attributes = {"brand": "Sushi Sushi", "brand_wikidata": "Q122915060", "extras": Categories.RESTAURANT.value}
    allowed_domains = ["kwefa302.api.sanity.io"]
    start_urls = ['https://kwefa302.api.sanity.io/v2021-08-31/data/query/production?query=*[_type == "storeData"]']

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["result"]:
            if not location["enabled"]:
                continue

            item = DictParser.parse(location)
            item["ref"] = location.get("store_id", location.get("_id"))
            item["branch"] = item["name"]
            item["street_address"] = clean_address([location.get("address_line_01"), location.get("address_line_02")])

            if item["state"]:
                item["state"] = item["state"].upper()

            if item["postcode"]:
                item["postcode"] = str(item["postcode"])

            if item["phone"] and "CALL ME" in item["phone"]:
                item.pop("phone", None)

            # 2024-07-18 Spider produces low quality coordinates, so we reject all for now.
            # https://github.com/alltheplaces/alltheplaces/issues/8683
            item["lat"] = None
            item["lon"] = None

            yield item
