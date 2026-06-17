from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.spiders.chiquito_gb import ChiquitoGBSpider


class BananaTreeGBSpider(ChiquitoGBSpider):
    name = "banana_tree_gb"
    item_attributes = {"brand": "Banana Tree", "brand_wikidata": "Q123013837"}
    sitemap_urls = ["https://bananatree.co.uk/sitemap.xml"]

    def parse_item(self, item: Feature, response: Response, **kwargs) -> Iterable[Feature]:
        item["branch"] = response.xpath("//title/text()").get("").split("|")[0].strip()
        yield item
