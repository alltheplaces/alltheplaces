import json

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class SchoolLockerAUSpider(Spider):
    name = "school_locker_au"
    item_attributes = {"brand": "School Locker", "brand_wikidata": "Q126176270"}
    start_urls = ["https://schoollocker.com.au/pages/store-finder"]

    def parse(self, response):
        stores_data = json.loads(response.xpath('//*[@id="sf-store-data"]/text()').get())
        for store in stores_data:
            if merge_address_lines(store.get("address")):
                item = DictParser.parse(store)
                item["street_address"] = merge_address_lines(store.get("address"))
                apply_category(Categories.SHOP_CLOTHES, item)
                yield item
