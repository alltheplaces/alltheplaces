from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MercatoITSpider(SitemapSpider, StructuredDataSpider):
    name = "mercato_it"
    item_attributes = {"brand": "Mercatò", "brand_wikidata": "Q127389715"}
    sitemap_urls = ["https://www.mymercato.it/sitemap.xml"]
    sitemap_rules = [(r"https://www.mymercato.it/punti-vendita/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = [["Store", "GroceryStore"]]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "MERCATO' BIG" in item["name"]:
            item["branch"] = item["name"].removeprefix("MERCATO' BIG ")
            item["name"] = "MERCATO' BIG"
        elif "MERCATO' LOCAL" in item["name"]:
            item["branch"] = item["name"].removeprefix("MERCATO' LOCAL")
            item["name"] = "MERCATO' LOCAL"
        elif "MERCATO' EXTRA" in item["name"]:
            item["branch"] = item["name"].removeprefix("MERCATO' EXTRA")
            item["name"] = "MERCATO' EXTRA"
        else:
            item["branch"] = item["name"].removeprefix("MERCATO'")
            item["name"] = "MERCATO'"
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
