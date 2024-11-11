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
        content = response.xpath("//meta[@property='og:description']/@content").get()
        if "Tel:" in content:
            item = Feature()
            address = content.split("Tel:")[0].strip()
            item["addr_full"] = address
            postcode = address.split(",")[-1].strip()
            # Last address element should be postcode but comma between county and postcode is often missing
            cleaner_postcode = postcode.split(" ")
            postcode = " ".join(cleaner_postcode[-2:])
            item["postcode"] = postcode
            item["ref"] = item["website"] = response.url
            yield item
