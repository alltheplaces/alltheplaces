from locations.categories import Access, Categories, Fuel, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider


class EngenSpider(JSONBlobSpider):
    name = "engen"
    item_attributes = {"brand": "Engen", "brand_wikidata": "Q3054251"}
    start_urls = ["https://engen-admin.engen.co.za/api/service-stations/all"]
    locations_key = ["response", "data", "stations"]

    def post_process_item(self, item, response, location):
        item["ref"] = location["internal_id"]
        item["branch"] = location.pop("company_name").replace(self.item_attributes["brand"], "").strip()
        item["phone"] = location.pop("mobile")

        if location.get("country_name") == "DRC":  # has incorrect country_code of ZA
            item["country"] = "CD"
        if location.get("country_name") == "eSwatini":  # has incorrect country_code of ZA
            item["country"] = "SZ"

        postcode = location.pop("street_postal_code")
        if postcode and postcode != "0":
            location["postcode"] = postcode

        item["street_address"] = item.pop("street")
        try:
            int(item["street_address"].split(" ", 1)[0])
            item["housenumber"] = item["street_address"].split(" ", 1)[0]
            item["street"] = item["street_address"].split(" ", 1)[1]
        except ValueError:
            pass

        if "Quickshop" in location.get("rental_units", ""):
            shop_item = item.deepcopy()
            shop_item["ref"] = str(item.get("ref")) + "-attached-shop"
            shop_item.pop("email")
            shop_item.pop("phone")
            shop_item.update(
                {
                    "brand": "Quickshop",
                    "brand_wikidata": "Q122764368",
                }
            )
            apply_category(Categories.SHOP_CONVENIENCE, shop_item)
            yield shop_item

        apply_category(Categories.FUEL_STATION, item)

        if location["station_types"] == "Truck Stop":
            item["name"] = "Truck Stop"
            apply_yes_no(Access.HGV, item, True)
        else:
            item["name"] = "Engen"

        apply_yes_no(Fuel.ADBLUE, item, "AdBlue" in location["rental_units"])

        yield item
