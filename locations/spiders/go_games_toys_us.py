from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class GoGamesToysUSSpider(WPStoreLocatorSpider):
    name = "go_games_toys_us"
    item_attributes = {
        "brand_wikidata": "Q108312837",
        "brand": "Go! Games & Toys",
        "extras": Categories.SHOP_TOYS.value,
    }
    allowed_domains = [
        "goretailgroup.com",
    ]
    iseadgg_countries_list = ["US"]
    search_radius = 500
    max_results = 100
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item["name"] == "Attic Salt":
            item["brand"] = "Attic Salt"
            item["brand_wikidata"] = "Q108409773"

        # "name" field contains:
        #   - "Attic Salt"
        #   - "Go! Games & Toys"
        #   - "Go! Calendars Games & Toys"
        #   - "Go! Calendars, Games and Toys"
        #   - "Go!CalendarsGamesToys&Books"
        #   - etc
        # Due to the inconsistencies, we'll just drop the field completely
        # so that the "brand" value is used instead. There is no branch name
        # to extract from the "name" field.
        item.pop("name", None)

        yield item
