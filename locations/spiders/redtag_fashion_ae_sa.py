from typing import Any

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RedtagFashionAESASpider(Spider):
    name = "redtag_fashion_ae_sa"
    item_attributes = {
        "brand": "Red Tag",
        "brand_wikidata": "Q132891092",
    }

    def start_requests(self):
        countries = ["Saudi Arabia", "UAE"]
        for country in countries:
            yield Request(
                url=f"https://redtagfashion.com/locations/locations.php?country={country}",
                meta={"country": country},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["ref"] = f"{response.meta['country']}_{store['storecode']}"
            item["street_address"] = item.pop("addr_full")

            if hours := store.get("timming"):  # Note the misspelling in the API
                oh = OpeningHours()
                oh.add_ranges_from_string(hours)
                item["opening_hours"] = oh

            apply_category(Categories.SHOP_CLOTHES, item)

            apply_yes_no("homeware", item, store.get("homeware") == "1")
            apply_yes_no("cosmetics", item, store.get("cosmetics") == "1")

            yield item
