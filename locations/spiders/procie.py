import re
from typing import Iterable

from scrapy.http import TextResponse
from unidecode import unidecode

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", unidecode(value).lower()).strip("-")


class ProcieSpider(UberallSpider):
    name = "procie"
    item_attributes = {"name": "PRO&Cie", "brand": "PRO&Cie", "brand_wikidata": "Q3406142"}
    key = "sKsUWiL9UlDoQ7pm9PisaUkhVJSM6K"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        # Shops are run by independent owners, the part after the brand names the business
        name = item.pop("name").strip()
        item["branch"] = re.sub(r"^pro&cie\s*-\s*", "", name, flags=re.IGNORECASE)

        item["website"] = "https://www.procie.com/nos-magasins.html#!/l/{}/{}/{}".format(
            slugify(location["city"]), slugify(location["streetAndNumber"] or ""), location["id"]
        )

        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
