from locations.categories import Categories
from locations.storefinders.yext import YextSpider

SUNGLASS_HUT_SHARED_ATTRIBUTES = {
    "brand": "Sunglass Hut",
    "brand_wikidata": "Q136311",
    "extras": Categories.OPTOMETRIST.value,
}
LENSCRAFTERS_ATTRIBUTES = {"brand": "LensCrafters", "brand_wikidata": "Q6523209"}
PEARLE_VISION_ATTRIBUTES = {"brand": "Pearle Vision", "brand_wikidata": "Q2231148"}
TARGET_OPTICAL_ATTRIBUTES = {"brand": "Target Optical", "brand_wikidata": "Q19903688"}

SUNGLASS_HUT_BRANDS = {
    "LC_OD_AT_MACY'S": LENSCRAFTERS_ATTRIBUTES | {"extras": Categories.OPTOMETRIST.value},
    "LC_OD_NON_TEXAS": LENSCRAFTERS_ATTRIBUTES | {"extras": Categories.OPTOMETRIST.value},
    "LC_OD_TEXAS": LENSCRAFTERS_ATTRIBUTES | {"extras": Categories.OPTOMETRIST.value},
    "LENSCRAFTERS": LENSCRAFTERS_ATTRIBUTES | {"extras": Categories.SHOP_OPTICIAN.value},
    "LENSCRAFTERS_CA": LENSCRAFTERS_ATTRIBUTES | {"extras": Categories.SHOP_OPTICIAN.value},
    "OAKLEY": {"brand": "Oakley", "brand_wikidata": "Q161906", "extras": Categories.SHOP_OPTICIAN.value},
    "PEARLE_VISION": PEARLE_VISION_ATTRIBUTES | {"extras": Categories.SHOP_OPTICIAN.value},
    "PV_OD": PEARLE_VISION_ATTRIBUTES | {"extras": Categories.OPTOMETRIST.value},
    "RAY-BAN": {"brand": "Ray-Ban", "brand_wikidata": "Q653941", "extras": Categories.SHOP_OPTICIAN.value},
    "SUNGLASS_HUT": SUNGLASS_HUT_SHARED_ATTRIBUTES,
    "TARGET_OPTICAL": TARGET_OPTICAL_ATTRIBUTES | {"extras": Categories.SHOP_OPTICIAN.value},
    "TO_OD": TARGET_OPTICAL_ATTRIBUTES | {"extras": Categories.OPTOMETRIST.value},
}


class SunglassHutSpider(YextSpider):
    name = "sunglass_hut"
    api_key = "2f3a9dda00e30159f040cb1107e21927"
    api_version = "20220511"

    def parse_item(self, item, location):
        item.pop("twitter", None)
        item.pop("instagram", None)
        if item["website"] is not None and "?" in item["website"]:
            item["website"] = item["website"].split("?")[0]  # strip yext tracking
        if brand := location.get("c_pagesSubscription"):
            if brand in SUNGLASS_HUT_BRANDS:
                item.update(SUNGLASS_HUT_BRANDS.get(brand))
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{brand}")
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/no_brand")

        yield item
