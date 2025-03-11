from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiVNSpider(JSONBlobSpider):
    name = "mitsubishi_vn"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    start_urls = ["https://www.mitsubishi-motors.com.vn/webapi/v1/wp/dealerNetwork"]
    locations_key = "items"

    def pre_process_data(self, feature):
        feature.update(feature.pop("acf"))
        feature.update(feature.pop("dealer_location"))

    def post_process_item(self, item, response, location):
        phone = location.get("phone", "")

        phone_sales = []
        if isinstance(location.get("phone_sales", []), list):
            phone_sales = [p["phone_sale"] for p in location["phone_sales"]]

        phone_services = []
        if isinstance(location.get("phone_services", []), list):
            phone_services = [p["phone_service"] for p in location["phone_services"]]

        item["phone"] = "; ".join(filter(None, [phone] + phone_sales + phone_services))

        services = [s["id"] for s in location.get("dealer_service", [])]
        if 219 or 364 in services:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_REPAIR, item, 220 in services)
            apply_yes_no(Extras.CAR_PARTS, item, 220 in services)
            apply_yes_no(Extras.USED_CAR_SALES, item, 364 in services)
        elif 220 in services:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            apply_yes_no(Extras.CAR_PARTS, item, 220 in services)
            apply_yes_no(Extras.USED_CAR_SALES, item, 364 in services)

        # TODO: hours
        yield item
