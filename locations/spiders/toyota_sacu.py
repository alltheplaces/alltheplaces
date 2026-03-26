from copy import deepcopy
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT

BRANDS = {
    "toyotaSupplier": TOYOTA_SHARED_ATTRIBUTES,
    "lexusSupplier": {"brand": "Lexus", "brand_wikidata": "Q35919"},
    "hinoSupplier": {"brand": "Hino Motors", "brand_wikidata": "Q867667"},
}

CATEGORIES_SHOP = {
    "toyotaSupplier": Categories.SHOP_CAR,
    "lexusSupplier": Categories.SHOP_CAR,
    "hinoSupplier": Categories.SHOP_TRUCK,
}

CATEGORIES_SERVICE = {
    "toyotaSupplier": Categories.SHOP_CAR_REPAIR,
    "lexusSupplier": Categories.SHOP_CAR_REPAIR,
    "hinoSupplier": Categories.SHOP_TRUCK_REPAIR,
}


class ToyotaSacuSpider(JSONBlobSpider):
    name = "toyota_sacu"
    start_urls = ["https://api-toyota.azure-api.net/suppliers?filter[where][supplierType]=dealer"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = "https://www.toyota.co.za/dealership/" + feature["name"].lower().replace(" ", "-")
        if item["state"] in ["Botswana", "Lesotho", "Eswatini", "Namibia"]:
            item["country"] = item.pop("state")
        else:
            item["country"] = "ZA"
        for brand, attributes in BRANDS.items():
            if feature[brand] == "Y":
                branded_item = deepcopy(item)
                branded_item["ref"] = f"{item['ref']}-{brand}"
                branded_item["brand"] = attributes["brand"]
                branded_item["brand_wikidata"] = attributes["brand_wikidata"]

                service_item = deepcopy(branded_item)
                service_item["ref"] = f"{branded_item['ref']}-SERVICE"
                apply_category(CATEGORIES_SERVICE[brand], service_item)
                yield service_item

                if feature["serviceOnly"] != "Y":
                    shop_item = deepcopy(branded_item)
                    shop_item["ref"] = f"{branded_item['ref']}-SHOP"
                    apply_category(CATEGORIES_SHOP[brand], shop_item)
                    yield shop_item
