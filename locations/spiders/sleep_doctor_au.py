from locations.storefinders.shopapps import ShopAppsSpider


class SleepDoctorAUSpider(ShopAppsSpider):
    name = "sleep_doctor_au"
    item_attributes = {"brand": "Sleep Doctor", "brand_wikidata": "Q122435030"}
    key = "sleepdoctor-national.myshopify.com"

    def parse_item(self, item, location):
        # One of the locations has a longitude of 510.x instead of
        # 150.x so this typo needs to be fixed.
        if location["lng"].split(".", 1)[0] == "510":
            item["lat"] = location["lat"]
            item["lon"] = "150." + location["lng"].split(".", 1)[1]
        yield item
