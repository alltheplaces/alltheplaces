import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.items import Feature


class CookGBSpider(Spider):
    name = "cook_gb"
    item_attributes = {"brand": "Cook", "brand_wikidata": "Q5013417"}
    start_urls = ["https://www.cookfood.net/shops"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.xpath('//div[@class="shopinfo"]')
        for location in data:
            item = Feature()
            slug = location.xpath("h2//a/@href").get()
            item["website"] = "https://www.cookfood.net" + slug
            item["ref"] = slug
            item["branch"] = location.xpath("h2//a/text()").get()
            address = location.xpath("p//text()").get()
            if "t: " in address:
                item["addr_full"], item["phone"] = address.split("t: ")

            yield Request(item["website"], callback=self.parse_storepage, cb_kwargs={"item": item})

    def parse_storepage(self, response, item):
        item["lat"] = re.search(r"(?<=lat: )[^,]+", response.text).group(0)
        item["lon"] = re.search(r"(?<=lng: )[^,]+", response.text).group(0)

        yield item
