import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class KrispyKremeTWSpider(Spider):
    name = "krispy_kreme_tw"
    item_attributes = {"brand": "Krispy Kreme", "brand_wikidata": "Q1192805"}
    start_urls = ["http://www.krispykreme.com.tw/store/store.aspx"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@id="store_content"]'):
            location_info = location.xpath('.//*[@class="info"]')
            item = Feature()
            item["ref"] = item["branch"] = location_info.xpath("./h1/text()").get()
            item["addr_full"] = location_info.xpath("./p[1]/text()").get()
            item["phone"] = location_info.xpath("./p[2]/text()").get()
            map_url = location.xpath(".//iframe[contains(@src, 'map')]/@src").get("")
            if coordinates := re.search(r"lat=([-.\d]+)&lng=([-.\d]+)", map_url):
                item["lat"], item["lon"] = coordinates.groups()
            item["website"] = response.url
            yield item
