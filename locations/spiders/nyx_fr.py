from typing import Iterable

from pyproj import Geod
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class NYXFRSpider(JSONBlobSpider):
    name = "nyx_fr"
    item_attributes = {"brand": "Nyx", "brand_wikidata": "Q23671513"}
    locations_key = ["storelocatorresults", "stores"]
    needs_json_request = True
    name_is_branch = True
    geod_obj = Geod(ellps="WGS84")
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    async def start(self):
        for lat, lon in country_iseadgg_centroids("FR", 94):
            yield JsonRequest(
                "https://www.nyxcosmetics.fr/on/demandware.store/"
                "Sites-nyx-fr-v2-Site/fr_FR/Stores-Search"
                f"?lat={lat}&long={lon}&searchDistance=100&ajax=true"
            )

    def is_shop_duplicate(self, shop1, shop2):
        same_city = (shop1.get("city") or "").strip().casefold() == (shop2.get("city") or "").strip().casefold()
        same_name = shop1["name"].strip().casefold() == shop2["name"].strip().casefold()
        same_phone = bool(shop1.get("phone")) and shop1["phone"] == shop2.get("phone")

        addr1, addr2 = [
            merge_address_lines([shop["address1"], shop["address2"]]).strip().casefold() for shop in (shop1, shop2)
        ]
        same_address = bool(addr1) and addr1 == addr2

        distance = self.geod_obj.inv(shop1["longitude"], shop1["latitude"], shop2["longitude"], shop2["latitude"])[2]

        return (distance == 0 and same_address) or (
            same_city
            and (
                same_phone
                or (distance <= 250 and same_address)
                or (distance <= 250 and same_name and not (shop1.get("phone") and shop2.get("phone")))
            )
        )

    def extract_json(self, response):
        shops = [
            shop
            for shop in super().extract_json(response)
            if shop["name"].casefold().startswith("nyx ") and "bleu libellule" not in shop["name"].casefold()
        ]

        shops.sort(
            key=lambda shop: (
                -bool(shop["phone"]),
                -bool(shop["websiteUrl"]),
                -len(merge_address_lines([shop["address1"], shop["address2"]])),
                shop["id"],
            )
        )

        unique_shops = []
        for shop1 in shops:
            if not any(self.is_shop_duplicate(shop1, shop2) for shop2 in unique_shops):
                unique_shops.append(shop1)

        return unique_shops

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item["branch"].removeprefix("NYX Professional Makeup ")
        item["street_address"] = merge_address_lines([feature["address1"], feature["address2"]])

        apply_category(Categories.SHOP_COSMETICS, item)

        yield item
