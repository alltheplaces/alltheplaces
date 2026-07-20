from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MidasSpider(SitemapSpider, StructuredDataSpider):
    name = "midas"
    item_attributes = {"brand": "Midas", "brand_wikidata": "Q3312613"}
    allowed_domains = [
        "www.midas.es",
        "www.midas.be",
        "www.midas.fr",
        "www.midas.it",
        "www.midas.pt",
        "www.midas.ci",
    ]
    sitemap_urls = [f"https://{domain}/sitemap.xml" for domain in allowed_domains]
    sitemap_rules = [
        ("/garages/", "parse_sd"),
        ("/talleres-coche-moto-midas/", "parse_sd"),
        ("/autofficina-midas/", "parse_sd"),
        ("/oficina-auto-midas/", "parse_sd"),
        ("/centres-auto-midas/", "parse_sd"),
    ]
    wanted_types = ["AutoRepair"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if name := item.pop("name", None):
            item["branch"] = name.removeprefix("Midas ").strip() or None
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
