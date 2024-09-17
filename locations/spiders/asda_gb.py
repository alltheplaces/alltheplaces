from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.virtualearth import VirtualEarthSpider

CATEGORY_MAP = {
    "Filling Station": Categories.FUEL_STATION,
    "Living": Categories.SHOP_DEPARTMENT_STORE,
    "Supercentre": Categories.SHOP_SUPERMARKET,
    "Supermarket": Categories.SHOP_SUPERMARKET,
    "Superstore": Categories.SHOP_SUPERMARKET,
}


class AsdaGBSpider(VirtualEarthSpider):
    name = "asda_gb"
    item_attributes = {"brand": "Asda", "brand_wikidata": "Q297410"}
    dataset_id = "2c85646809c94468af8723dd2b52fcb1"
    dataset_name = "AsdaStoreLocator/asda_store"
    api_key = "AtAs6PiQ3e0HE187rJgUEqvoKcKfTklRKTvCN1X1mpumYE-Z4VQFvx62X7ff13t6"
    dataset_filter = "country Eq 'United Kingdom'"

    def parse_item(self, item: Feature, feature: dict, **kwargs):
        if feature["asda_store_type"] == "Collection Point":
            return

        if feature["asda_store_type"] == "Living":
            item["name"] = item["name"].replace("Living", "").strip()
        item["branch"] = item.pop("name")

        item["ref"] = feature["imp_id"]
        item["street_address"] = feature["street"]
        item["city"] = feature["town"]
        item["state"] = feature["county"]
        item["postcode"] = feature["post_code"]
        item["country"] = feature["country"]
        # Unfortunately this is a redirect, not the canonical URL
        item["website"] = "https://storelocator.asda.com/store/{}".format(feature["url_key"])
        # item["image"] = feature["store_photo_url"]  # TODO: find the root url for the images

        if cat := CATEGORY_MAP.get(feature["asda_store_type"]):
            apply_category(cat, item)
        else:
            self.crawler.stats.inc_value("atp/unmapped_category/{}".format(feature["asda_store_type"]))

        if feature["asda_service_24_hour"]:
            item["opening_hours"] = "24/7"

        apply_yes_no(Extras.TOILETS, item, feature["asda_service_customer_wc"])
        apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, feature["asda_service_disabled_facilities"])
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, feature["asda_service_baby_changing"])
        apply_yes_no(Extras.ATM, item, feature["asda_service_cash_machine"])

        yield item
