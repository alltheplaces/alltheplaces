import re

from scrapy import Request
from scrapy.http import Response

from locations.structured_data_spider import StructuredDataSpider


class TedoxDESpider(StructuredDataSpider):
    name = "tedox_de"
    item_attributes = {"brand": "tedox", "brand_wikidata": "Q2399946"}

    start_urls = ["https://www.tedox.de/shoplist/"]
    marker_pattern = r"ib_setMarker\(\W*(\d{1,2}\.\d+),\W*(\d{1,2}\.\d+),\W*'tedox .+?',\W*(\d+)\W*,.+?\);"

    def parse(self, response: Response):
        for lat, lon, id in re.findall(self.marker_pattern, response.text, re.DOTALL):
            yield Request(
                "https://www.tedox.de/shoplist/index/detail/?id=" + id,
                meta=dict(lat=lat, lon=lon),
                callback=self.parse_sd,
            )

    def post_process_item(self, item, response: Response, ld_data):
        item["lat"], item["lon"] = response.meta["lat"], response.meta["lon"]
        item["image"] = response.xpath('//p[@class="product-image"]/img/@src').get()
        yield item
