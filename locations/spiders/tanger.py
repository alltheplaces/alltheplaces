import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature


class TangerSpider(SitemapSpider):
    name = "tanger"
    item_attributes = {"brand": "Tanger Outlets", "brand_wikidata": "Q7682888"}
    sitemap_urls = ["https://www.tanger.com/robots.txt"]
    sitemap_rules = [(r"/location$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath('//li[@class="nav-item centerLink"]/a/text()').get()
        if lat := re.search(r"centerLatitude = (-?\d+\.\d+);", response.text):
            item["lat"] = lat.group(1)
        if lon := re.search(r"centerLongitude = (-?\d+\.\d+);", response.text):
            item["lon"] = lon.group(1)

        yield item
