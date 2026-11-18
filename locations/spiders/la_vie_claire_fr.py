from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LaVieClaireFRSpider(SitemapSpider, StructuredDataSpider):
    name = "la_vie_claire_fr"
    item_attributes = {"brand": "La Vie Claire", "brand_wikidata": "Q3213589"}
    sitemap_urls = ["https://magasins.lavieclaire.com/sitemap.xml"]
    sitemap_rules = [(r"https://magasins.lavieclaire.com/lavieclaire/fr/store/.*/\d+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "La Vie Claire chez" in item.get("name"):
            return
        item["branch"] = (
            (item.pop("name") or "")
            .removeprefix("Magasin Bio La Vie Claire ")
            .removeprefix("Magasin bio La Vie Claire ")
        )
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
