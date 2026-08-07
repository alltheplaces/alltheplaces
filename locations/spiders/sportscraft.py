from typing import Any, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class SportscraftSpider(JSONBlobSpider):
    name = "sportscraft"
    item_attributes = {"brand": "Sportscraft", "brand_wikidata": "Q7579966"}

    async def start(self) -> Any:
        yield JsonRequest(
            url="https://sportscraft-apgnext.frontastic.live/frontastic/action/apg-storelocator/getStoresList",
            data={"skus": [], "cartId": None},
            headers={
                "x-frontastic-access-token": "APIKEY",
                "frontastic-locale": "en_AU@AUD",
                "frontastic-currency": "AUD",
            },
        )

    def pre_process_data(self, feature: dict) -> None:
        coordinates = feature.get("coordinates") or {}
        feature["latitude"], feature["longitude"] = coordinates.get("lat"), coordinates.get("lng")

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("email", None)
        item.pop("country", None)
        item.pop("name", None)
        item["ref"] = feature["key"]
        item["branch"] = feature["storeName"].split("(", 1)[0].strip()
        item["street_address"] = clean_address([feature.get("address1"), feature.get("address2")])
        item["website"] = "https://www.sportscraft.com.au/store-locator/store-details?id=" + feature["key"]

        item["opening_hours"] = OpeningHours()
        for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
            if feature.get(f"hours_{day}_open") and feature.get(f"hours_{day}_close"):
                item["opening_hours"].add_ranges_from_string(
                    f"{day}: {feature[f'hours_{day}_open']}-{feature[f'hours_{day}_close']}"
                )

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
