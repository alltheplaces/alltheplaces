from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class TraficBESpider(UberallSpider):
    name = "trafic_be"
    item_attributes = {"brand": "Trafic", "brand_wikidata": "Q20732590"}
    key = "XE7J0F81JmOa0Wz7txJRunNoFPM5ub"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").title().removeprefix("Trafic ")
        item["ref"] = location.get("id")
        slug = f'{item["city"]}/{item["street_address"]}/{item["ref"]}'.lower().replace(" ", "-")
        item["website"] = item["extras"]["website:nl"] = f"https://trafic.com/nl_BE/winkels/#!/l/{slug}"
        item["extras"]["website:fr"] = f"https://trafic.com/fr_BE/magasins/#!/l/{slug}"

        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

        yield item
