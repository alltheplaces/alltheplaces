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

        if feature["asda_service_pharmacy"]:
            pharmacy_poi = self.create_pharmacy_poi(item)
            if pharmacy_poi:
                yield pharmacy_poi

        if feature["asda_service_cafe"]:
            cafe_poi = self.create_cafe_poi(item)
            if cafe_poi:
                yield cafe_poi

        if feature["asda_service_opticians"]:
            optician_poi = self.create_optician_poi(item)
            if optician_poi:
                yield optician_poi

        if feature["asda_service_petrol_station"]:
            petrol_poi = self.create_petrol_station_poi(item)
            if petrol_poi:
                yield self.create_petrol_station_poi(item)

        apply_yes_no(Extras.TOILETS, item, feature["asda_service_customer_wc"])
        apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, feature["asda_service_disabled_facilities"])
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, feature["asda_service_baby_changing"])
        apply_yes_no(Extras.ATM, item, feature["asda_service_cash_machine"])

        yield item

    def create_department_poi(self, store_item, poi_type, name_suffix, category):
        """Create separate POI for a department (pharmacy, café, etc.)"""
        poi = store_item.copy()

        # Create unique ref
        poi["ref"] = f"{store_item['ref']}_{poi_type}"

        # Clear store-specific fields
        poi.pop("shop", None)

        # Clear opening hours
        poi.pop("opening_hours", None)

        # Clear phone and website
        poi.pop("phone", None)
        poi.pop("website", None)

        # Clear store amenity extras
        if "extras" in poi:
            poi.pop("extras", None)

        # Set POI-specific fields
        apply_category(category, poi)
        poi["name"] = f"Asda {name_suffix}"
        poi.update(self.item_attributes)

        return poi

    def create_pharmacy_poi(self, store_item):
        """Create separate POI for pharmacy"""
        return self.create_department_poi(store_item, "pharmacy", "Pharmacy", Categories.PHARMACY)

    def create_cafe_poi(self, store_item):
        """Create separate POI for café"""
        return self.create_department_poi(store_item, "cafe", "Café", Categories.CAFE)

    def create_optician_poi(self, store_item):
        """Create separate POI for optician"""
        return self.create_department_poi(store_item, "optician", "Optician", Categories.SHOP_OPTICIAN)

    def create_petrol_station_poi(self, store_item):
        """Create separate POI for petrol station"""
        return self.create_department_poi(store_item, "fuel", "Petrol Station", Categories.FUEL_STATION)
