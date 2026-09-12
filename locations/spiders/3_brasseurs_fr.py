from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TroisBrasseursFRSpider(SitemapSpider, StructuredDataSpider):
    name = "3_brasseurs_fr"
    item_attributes = {"brand": "3 Brasseurs", "brand_wikidata": "Q3230326"}
    sitemap_urls = ["https://restaurants.3brasseurs.com/sitemap_pois.xml"]
    sitemap_rules = [(r"https://restaurants.3brasseurs.com/fr/france-FR/.*", "parse_sd")]
    wanted_types = ["Restaurant"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/3brasseurs/":
            item["facebook"] = None

        item["branch"] = item.pop("name").removeprefix("3 Brasseurs ")

        apply_category(Categories.RESTAURANT, item)
        yield item
