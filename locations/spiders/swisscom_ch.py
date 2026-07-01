import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser


class SwisscomCHSpider(SitemapSpider):
    name = "swisscom_ch"
    item_attributes = {"brand": "Swisscom", "brand_wikidata": "Q644324"}
    sitemap_urls = ["https://swisscomshops.swisscom.ch/en/sitemap.xml"]
    sitemap_rules = [(r"/en/[^/]+/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        ld = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').get())
        item = LinkedDataParser.parse_ld(ld["itemListElement"][0])
        if (name := item.pop("name")) and " - " in name:
            item["branch"] = name.split(" - ", 1)[1]
        apply_category(Categories.SHOP_TELECOMMUNICATION, item)
        yield item
