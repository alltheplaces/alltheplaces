import re
from typing import Any

import chompjs
import scrapy
from scrapy.http import Response

from locations.items import Feature


class LouisaCoffeeTWSpider(scrapy.Spider):
    name = "louisa_coffee_tw"
    item_attributes = {"brand": "路易莎咖啡", "brand_wikidata": "Q96390921"}
    start_urls = ["https://www.louisacoffee.co/assets/js/jquery.twzipcode.js"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for city in (chompjs.parse_js_object(re.search(r"var\s+data\s*=\s*([^;]+);", response.text).group(1))).keys():
            yield scrapy.Request(
                url="https://www.louisacoffee.co/visit_result",
                method="POST",
                body="data%5Bcounty%5D={}".format(city),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                },
                cb_kwargs={"city": city},
                callback=self.parse_details,
            )

    def parse_details(self, response, **kwargs):
        for store in response.xpath('//*[@class="col-md-1"]'):
            item = Feature()
            item["name"] = item["ref"] = store.xpath(".//@rel-store-name").get()
            item["addr_full"] = store.xpath(".//@rel-store-address").get()
            item["city"] = kwargs["city"]
            item["lat"] = store.xpath(".//@rel-store-lat").get()
            item["lon"] = store.xpath(".//@rel-store-lng").get()
            yield item
