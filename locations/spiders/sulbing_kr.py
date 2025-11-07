from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class SulbingKRSpider(scrapy.Spider):
    name = "sulbing_kr"
    item_attributes = {"brand_wikidata": "Q18156373"}
    start_urls = ["https://sulbing.com/bbs/board.php?bo_table=store&page=1"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for city in response.xpath('//*[@name="addr1"]/option/text()').getall():
            if city == "도/시":
                continue
            yield scrapy.Request(url=f"https://sulbing.com/store/?addr1={city}", callback=self.parse_location)

    def parse_location(self, response):
        for location in response.xpath('//*[@class="searchResult"]'):
            item = Feature()
            item["branch"] = location.xpath("./a/@storename").get()
            item["street_address"] = location.xpath("./a/@address").get()
            item["lat"] = location.xpath("./a/@ly").get()
            item["lon"] = location.xpath("./a/@lx").get()
            item["ref"] = location.xpath("./a/@vid").get()
            item["addr_full"] = location.xpath('.//*[@class="address"]/text()').get()
            apply_category(Categories.CAFE, item)
            yield item
