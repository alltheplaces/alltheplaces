from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.central_england_cooperative import COOP_FOOD, set_operator
from locations.storefinders.uberall import UberallSpider

SOUTHERN_COOP = {"brand": "The Southern Co-operative", "brand_wikidata": "Q7569773"}
WELCOME = {"brand": "Welcome", "brand_wikidata": "Q123004215"}


class SouthernCoopSpider(UberallSpider):
    name = "southern_coop"
    key = "uvMckoaRcAUKR0LkkH03SVNyf7A4Lk"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        set_operator(SOUTHERN_COOP, item)
        if "Welcome" in item["name"]:
            item.update(WELCOME)
        else:
            item.update(COOP_FOOD)
        apply_category(Categories.SHOP_CONVENIENCE, item)

        item[
            "website"
        ] = f'https://southern.coop/store-locator/l/-/{location["city"]}/{location["streetAndNumber"]}/{location["id"]}'.lower().replace(
            " ", "-"
        )
        yield item
