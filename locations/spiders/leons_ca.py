from scrapy import Spider

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class LeonsCASpider(Spider):
    name = "leons_ca"
    item_attributes = {"brand_wikidata": "Q6524456"}
    start_urls = [
        "https://stores.shopapps.site/front-end/get_surrounding_stores.php?shop=leons-furniture.myshopify.com&latitude=0&longitude=0&max_distance=100000000&limit=10000000"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["street_address"] = clean_address([location.pop("address"), location.pop("address2")])
            item = DictParser.parse(location)
            item["extras"]["branch"] = item.pop("name")

            yield item
