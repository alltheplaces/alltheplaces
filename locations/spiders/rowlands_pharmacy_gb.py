from locations.storefinders.uberall import UberallSpider


class RowlandsPharmacyGBSpider(UberallSpider):
    name = "rowlands_pharmacy_gb"
    item_attributes = {"brand": "Rowlands Pharmacy", "brand_wikidata": "Q62663235"}
    key = "bwzEvjRHRFzJjkeRduLJgHcDYens3x"

    def post_process_item(self, item, response, location):
        if not location["ref"]:
            return None

        item["website"] = "https://rowlandspharmacy.co.uk/find-local-pharmacy#!/l/{}".format(
            "/".join([item["city"], item["street_address"], location["ref"]]).lower().replace(" ", "-")
        )

        yield item
