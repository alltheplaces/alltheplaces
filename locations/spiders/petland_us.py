from collections.abc import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PetlandUSSpider(WPStoreLocatorSpider):
    name = "petland_us"
    item_attributes = {"brand": "Petland", "brand_wikidata": "Q17111474"}
    allowed_domains = ["petland.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 500
    max_results = 100
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["email"] = None
        if feature["country"] not in ("USA", "United States"):
            return
        # Default WPSL hours left unedited by most stores
        if item["opening_hours"].as_opening_hours() == "Mo-Fr 09:00-17:00; Sa-Su closed":
            item["opening_hours"] = None
        apply_category(Categories.SHOP_PET, item)
        yield item
