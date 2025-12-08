import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class StarkDKSpider(scrapy.Spider):
    name = "stark_dk"
    item_attributes = {"brand": "Stark", "brand_wikidata": "Q16324560"}
    start_urls = ["https://www.stark.dk/forretninger"]

    def parse(self, response):
        for location in chompjs.parse_js_object(
            response.xpath('//*[@class="col-12"]').re_first(r"v-bind:stores=\s*\'\s*(\[.+?])\'")
        ):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            apply_category(Categories.SHOP_HARDWARE, item)
            yield item
