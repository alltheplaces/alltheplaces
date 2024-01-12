from locations.storefinders.uberall import UberallSpider


class RowlandsPharmacyGBSpider(UberallSpider):
    name = "rowlands_pharmacy_gb"
    item_attributes = {"brand": "Rowlands Pharmacy", "brand_wikidata": "Q62663235"}
    key = "bwzEvjRHRFzJjkeRduLJgHcDYens3x"

    def parse_item(self, item, feature, **kwargs):
        if not feature["ref"]:
            return None

        item["website"] = "https://rowlandspharmacy.co.uk/find-local-pharmacy#!/l/{}".format(
            "/".join([item["city"], item["street_address"], feature["ref"]]).lower().replace(" ", "-")
        )

        yield item
