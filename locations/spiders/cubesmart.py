import urllib.parse
from pathlib import Path

from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class CubeSmartSpider(SitemapSpider):
    name = "cubesmart"
    item_attributes = {
        "brand": "CubeSmart",
        "brand_wikidata": "Q5192200",
    }
    allowed_domains = ["www.cubesmart.com"]
    sitemap_urls = ["https://www.cubesmart.com/sitemap-facility.xml"]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "SelfStorage")
        item["lon"] = "-" + item["lon"]
        item["ref"] = Path(urllib.parse.urlsplit(response.url).path).stem
        yield item
