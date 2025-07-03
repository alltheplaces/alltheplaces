import html
import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class NeonetPLSpider(SitemapSpider):
    name = "neonet_pl"
    item_attributes = {"brand": "Neonet", "brand_wikidata": "Q11790622"}
    sitemap_urls = ["https://sklepy.neonet.pl/sitemap.xml"]
    sitemap_rules = [(r"/polska/.*[0-9]$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(html.unescape(response.xpath('//*[@type="application/ld+json"]/text()').get()))
        for entry in data.get("@graph") or []:
            if entry.get("@type") == "LocalBusiness":
                item = LinkedDataParser.parse_ld(entry)
                yield item
                return
