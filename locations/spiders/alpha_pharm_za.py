import ast

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class AlphaPharmZASpider(JSONBlobSpider):
    name = "alpha_pharm_za"
    item_attributes = {
        "brand": "Alpha Pharm",
        "brand_wikidata": "Q116487265",
    }
    start_urls = [
        "https://www.alphapharmacies.co.za/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=8a9c5c9229&load_all=1&layout=1"
    ]

    def pre_process_data(self, location, **kwargs):
        location["street_address"] = location.pop("street")

    def post_process_item(self, item, response, location):
        # n.b. Name is used as the branding for the location, do not move it to brand

        if location["categories"] is not None:
            categories = location["categories"].split(",")
            # Categories:
            # 18: Pharmacy
            # 20: AlphaDoc
            # 21: Clinic
            apply_yes_no(Extras.PHOTO_PRINTING, item, "22" in categories, False)  # Described as Kodak machine
            # 23: AlphaREWARDS
            # 24: Essence Stock
            # 25: Covid19 Vaccine

        location_hours = ast.literal_eval(location["open_hours"])
        oh = OpeningHours()
        for day in location_hours:
            for times in location_hours[day]:
                oh.add_ranges_from_string(day + " " + times)
        item["opening_hours"] = oh.as_opening_hours()

        yield item
