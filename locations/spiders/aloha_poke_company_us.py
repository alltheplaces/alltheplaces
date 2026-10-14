from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AlohaPokeCompanyUSSpider(WPStoreLocatorSpider):
    name = "aloha_poke_company_us"
    item_attributes = {"brand": "Aloha Pokē Co", "brand_wikidata": "Q111231031"}
    allowed_domains = ["www.alohapokeco.com"]
    start_urls = [
        "https://www.alohapokeco.com/wp-admin/admin-ajax.php?action=store_search&lat=41.8781136&lng=-87.6297982&autoload=1"
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        apply_category(Categories.FAST_FOOD, item)
        yield item
