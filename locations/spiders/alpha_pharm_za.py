from locations.categories import Extras, apply_yes_no
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class AlphaPharmZASpider(AgileStoreLocatorSpider):
    name = "alpha_pharm_za"
    item_attributes = {
        "brand": "Alpha Pharm",
        "brand_wikidata": "Q116487265",
    }
    allowed_domains = ["alphapharmacies.co.za"]

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

        yield item
