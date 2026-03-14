from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class BananaTreeGBSpider(FrankieAndBennysGBSpider):
    name = "banana_tree_gb"
    item_attributes = {"brand": "Banana Tree", "brand_wikidata": "Q123013837"}
    sitemap_urls = ["https://bananatree.co.uk/sitemap.xml"]

    def parse_item(self, item: Feature, response: Response, **kwargs) -> Iterable[Feature]:
        item["branch"] = response.xpath("//title/text()").get("").split("|")[0].strip()
        yield item
