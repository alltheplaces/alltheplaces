import json
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class KidStrongUSSpider(SitemapSpider):
    name = "kid_strong_us"
    item_attributes = {"brand": "KidStrong", "brand_wikidata": "Q125705878"}
    sitemap_urls = ["https://www.kidstrong.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/?$", "parse")]

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        item = DictParser.parse(
            next(
                node
                for node in json.loads(response.xpath('//script[@data-hid="ld-graph"]/text()').get())["@graph"]
                if "LocalBusiness" in node["@type"]
            )
        )
        item["ref"] = response.url.rstrip("/").rpartition("/")[2]
        item["branch"] = item.pop("name").removeprefix("KidStrong ")
        item["website"] = response.url
        apply_category(Categories.GYM, item)
        yield item
