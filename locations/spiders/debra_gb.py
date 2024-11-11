from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature


class DebraGBSpider(SitemapSpider):
    name = "debra_gb"
    item_attributes = {"brand": "Debra", "brand_wikidata": "Q104535435"}
    sitemap_urls = ["https://www.debra.org.uk/sitemap.xml"]
    sitemap_rules = [(r"uk/charity-shop/[-\w]+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["addr_full"] = response.xpath("//address/text()").get()
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["ref"] = item["website"] = response.url
        yield item
