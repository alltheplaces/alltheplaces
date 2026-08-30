from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

TOLLENS = {"brand": "Tollens", "brand_wikidata": "Q127515008"}
ZOLPAN = {"brand": "Zolpan", "brand_wikidata": "Q126875048"}


class TollensFRSpider(SitemapSpider, StructuredDataSpider):
    name = "tollens_fr"
    # tollens.com lists the whole Cromology retail network: Tollens and Zolpan
    # branded stores, plus some co-branded "Tollens Zolpan" ones.
    item_attributes = TOLLENS
    sitemap_urls = ["https://www.tollens.com/sitemap.xml"]
    sitemap_rules = [(r"/nos-magasins/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    # Every store page footer links the same brand-wide page, misattributed on Zolpan stores.
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        name = item.pop("name").removeprefix("Magasin de Peinture ")
        lowered = name.lower()
        if "zolpan" in lowered and "tollens" not in lowered:
            item.update(ZOLPAN)

        branch = name
        for prefix in ("Tollens", "Zolpan"):
            branch = branch.removeprefix(prefix + " ").removeprefix(prefix.upper() + " ")
        item["branch"] = branch

        apply_category(Categories.SHOP_PAINT, item)
        yield item
