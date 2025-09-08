import re
from typing import Any

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.items import Feature
from locations.storefinders.yext import YextSpider


class MaxMaraFashionGroupSpider(YextSpider):
    name = "max_mara_fashion_group"
    api_key = "51226541fc55f7ab950c3ec23be24c99"
    brands = {
        "DT": {"brand": "Intrend", "brand_wikidata": "Q136159133"},
        "FM": {"brand": "Fashion Market", "brand_wikidata": "Q136160048"},
        "IB": {"brand": "iBlues", "brand_wikidata": "Q136158956"},
        "LM": {"brand": "EMME", "brand_wikidata": "Q136159991"},
        "MA": {"brand": "Marella", "brand_wikidata": "Q118111682"},
        "MC": {"brand": "MAX&Co.", "brand_wikidata": "Q120570926"},
        "MM": {"brand": "Max Mara", "brand_wikidata": "Q1151774"},
        "MR": {"brand": "Marina Rinaldi", "brand_wikidata": "Q2349550"},
        "PB": {"brand": "Pennyblack", "brand_wikidata": "Q136159211"},
        "PS": {"brand": "Persona", "brand_wikidata": "Q136159149"},
        "SP": {"brand": "Sportmax", "brand_wikidata": "Q56316823"},
        "WE": {"brand": "Weekend Max Mara", "brand_wikidata": "Q136159038"},
    }

    def parse_item(self, item: Feature, location: dict, **kwargs: Any) -> Any:
        if brand_id := location.get("c_brand"):
            if brand_id not in self.brands.keys():
                self.logger.error(
                    "Unknown brand code '{}' with name '{}'.".format(brand_id, location.get("c_internalName"))
                )
            else:
                item["brand"] = self.brands[location["c_brand"]]["brand"]
                item["brand_wikidata"] = self.brands[location["c_brand"]]["brand_wikidata"]
        else:
            # Unbranded features are headquarters, corporate offices, etc.
            # Ignore such features.
            return
        if branch_name := location.get("c_internalName"):
            if item["brand"]:
                item["branch"] = re.sub(
                    r"^(\s*" + re.escape(item["brand"]) + r")\s*", "", branch_name, flags=re.IGNORECASE
                )
            else:
                item["branch"] = branch_name
        if website_url := location.get("c_pagesURL"):
            item["website"] = website_url.split("?", 1)[0]
        else:
            item.pop("website", None)
        apply_category(Categories.SHOP_CLOTHES, item)
        apply_clothes([Clothes.WOMEN], item)
        yield item
