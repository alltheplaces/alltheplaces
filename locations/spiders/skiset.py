import json
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class SkisetSpider(SitemapSpider):
    name = "skiset"
    item_attributes = {"brand": "Skiset", "brand_wikidata": "Q48747223"}
    sitemap_urls = ["https://www.skiset.com/sitemap.xml"]
    sitemap_rules = [(r"https://www\.skiset\.com/.*/magasins/.*", "parse")]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        start = response.text.index("window.appConfig=") + len("window.appConfig=")
        shop = json.JSONDecoder().raw_decode(response.text[start:])[0]["shop"]["map"]
        if shop is None:  # a few shop pages have no address or map
            return
        item = DictParser.parse(shop)
        item["branch"] = item.pop("name").removeprefix("Skiset ")
        item["website"] = response.url
        apply_category(Categories.SHOP_SPORTS, item)
        yield item
