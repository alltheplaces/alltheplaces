from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class BricomarcheFRSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "bricomarche_fr"
    item_attributes = {"brand": "Bricomarché", "brand_wikidata": "Q2925147"}
    sitemap_urls = ["https://www.bricomarche.com/sitemap/Store-BM-fr-EUR"]
    sitemap_rules = [(r"/magasin/", "parse_sd")]
    wanted_types = ["HomeAndConstructionBusiness"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        ld_data["address"]["postalCode"] = str(ld_data["address"]["postalCode"]).zfill(5)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = item["website"].rstrip("/").split("/")[-1]
        item["branch"] = item.pop("name").removeprefix("Bricomarché ")
        item.pop("image", None)
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
