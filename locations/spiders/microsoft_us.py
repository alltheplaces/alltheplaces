from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.virtualearth import VirtualEarthSpider


class MicrosoftUSSpider(VirtualEarthSpider):
    name = "microsoft_us"
    item_attributes = {"brand": "Microsoft", "brand_wikidata": "Q2283", "nsi_id": "N/A"}
    dataset_id = "af8a315fb81847628946aafc6963e2b1"
    dataset_name = "CorporateOfficeStores/MicrosoftSalesOffices"
    api_key = "Akc3VL2S4OzK8I1l0zkWDYeK6K30AcDc997Num5aHlz5A-4rJGnArLkZTrgv_asB"
    dataset_filter = "1 Eq 1"
    dataset_select = "*"

    def parse_item(self, item: Feature, feature: dict):
        if ": " in item["name"]:
            item["name"], item["branch"] = item["name"].split(": ")

        if item["name"] == "Microsoft Experience Center":
            apply_category(Categories.SHOP_ELECTRONICS, item)
        else:
            apply_category(Categories.OFFICE_COMPANY, item)

        yield item
