from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KennardsSelfStorageNZSpider(SitemapSpider, StructuredDataSpider):
    name = "kennards_self_storage_nz"
    item_attributes = {"brand": "Kennards Storage", "brand_wikidata": "Q115565997"}
    sitemap_urls = ["https://www.kennards.co.nz/sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    search_for_twitter = False
    search_for_facebook = False

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        # A described specification covers 24 hour customer access, not office hours
        if isinstance(rules := ld_data.get("openingHoursSpecification"), list):
            ld_data["openingHoursSpecification"] = [rule for rule in rules if not rule.get("description")]

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        # Every location incorrectly states an Australian addressCountry
        item["country"] = "NZ"
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
