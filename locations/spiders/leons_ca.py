from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class LeonsCASpider(Spider):
    name = "leons_ca"
    item_attributes = {"brand": "Leon's", "brand_wikidata": "Q6524456"}
    start_urls = [
        "https://stores.shopapps.site/front-end/get_surrounding_stores.php?shop=leons-furniture.myshopify.com&latitude=0&longitude=0&max_distance=100000000&limit=10000000"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["street_address"] = merge_address_lines([location.pop("address"), location.pop("address2")])
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            apply_category(Categories.SHOP_FURNITURE, item)
            yield item
