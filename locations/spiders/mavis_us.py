from typing import Iterable
from urllib.parse import urljoin

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.ntb_us import NtbUSSpider

MAVIS_TIRES = {"name": "Mavis Tires & Brakes", "brand": "Mavis", "brand_wikidata": "Q65058420"}
MAVIS_DISCOUNT = {"name": "Mavis Discount Tire", "brand": "Mavis", "brand_wikidata": "Q65058420"}
TIRE_KINGDOM = {"brand": "Tire Kingdom", "brand_wikidata": "Q17090159"}
TUFFY = {"brand": "Tuffy", "brand_wikidata": "Q17125314"}
JACK_WILLIAMS = {"name": "Jack Williams Tire & Auto", "brand": "Jack Williams Tire & Auto"}


class MavisUSSpider(JSONBlobSpider):
    name = "mavis_us"
    start_urls = ["https://www.mavis.com/locations/all-stores/"]

    brands = {
        "Mavis Tire": (MAVIS_TIRES, Categories.SHOP_TYRES),
        "Melvin's Tire": (MAVIS_TIRES, Categories.SHOP_TYRES),
        "Mavis Discount": (MAVIS_DISCOUNT, Categories.SHOP_TYRES),
        "NTB Tire & Service Centers": (NtbUSSpider.item_attributes, Categories.SHOP_CAR_REPAIR),
        "Tire Kingdom Service Centers": (TIRE_KINGDOM, Categories.SHOP_TYRES),
        "Tuffy Tire & Auto": (TUFFY, Categories.SHOP_TYRES),
        "Jack Williams Tire & Auto": (JACK_WILLIAMS, Categories.SHOP_CAR_REPAIR),
    }

    def extract_json(self, response: Response) -> list:
        stores = []
        for state_wise_stores_list in chompjs.parse_js_object(
            (chompjs.parse_js_object(response.xpath('//script[contains(text(),"fullAddress")]/text()').get())[-1])
        )[-1]["children"][-1]["stores"].values():
            stores.extend(state_wise_stores_list)
        return stores

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("latLng"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        label = feature["storeHeader"]["fields"]["myStoreLabel"]
        for prefix in self.brands.keys():
            if label.startswith(prefix):
                brand, cat = self.brands[prefix]
                item.update(brand)
                apply_category(cat, item)
                break
        else:
            item["name"] = label
            apply_category(Categories.SHOP_TYRES, item)

        item["website"] = urljoin("https://www.mavis.com/locations/", feature.get("slug"))
        yield item
