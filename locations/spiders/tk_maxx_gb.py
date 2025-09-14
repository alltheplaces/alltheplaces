from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class TkMaxxGBSpider(YextAnswersSpider):
    name = "tk_maxx_gb"
    STORE_TYPES = {
        "TKMAXX": {"brand": "TK Maxx", "brand_wikidata": "Q23823668"},
        "HOMESENSE": {"brand": "Homesense", "brand_wikidata": "Q16844433"},
    }
    api_key = "ce8e33e14f7f6706a1a86e05e440d1a0"
    experience_key = "tk-maxx-search-experience"
    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"
    locale = "en-GB"
    drop_attributes = {"contact:instagram"}

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item["website"] = (
            item["website"]
            + "/uk/en/store/"
            + item["city"].lower().replace(" ", "-")
            + "/"
            + item["street_address"].lower().replace(" ", "-")
            + "/"
            + item["ref"]
        )
        if "homesense" in item["name"].lower():
            item.update(self.STORE_TYPES.get("HOMESENSE"))
            apply_category(Categories.SHOP_INTERIOR_DECORATION, item)
            item["branch"] = item.pop("name").replace("Homesense ", "")
        else:
            item.update(self.STORE_TYPES.get("TKMAXX"))
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
