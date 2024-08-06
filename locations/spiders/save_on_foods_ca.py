from scrapy import Spider

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class SaveOnFoodsCASpider(Spider):
    name = "save_on_foods_ca"
    item_attributes = {"brand": "Save-On-Foods", "brand_wikidata": "Q7427974"}
    start_urls = ["https://storefrontgateway.saveonfoods.com/api/stores"]

    def parse(self, response):
        for store in response.json()["items"]:

            item = DictParser.parse(store)
            item["lat"] = store["location"]["latitude"]
            item["lon"] = store["location"]["longitude"]

            item["street_address"] = clean_address(
                [store["addressLine1"], store["addressLine2"], store["addressLine3"]]
            )
            item["ref"] = store["retailerStoreId"]
            # StoreHours provided by the API but not parsed by this scraper; please add
            yield item
