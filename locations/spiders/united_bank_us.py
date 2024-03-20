from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.rio_seo import RioSeoSpider


class UnitedBankUSSpider(RioSeoSpider):
    name = "united_bank_us"
    item_attributes = {"brand": "United Bank", "brand_wikidata": "Q16920636"}
    allowed_domains = ["locations.bankwithunited.com"]
    start_urls = [
        "https://maps.locations.bankwithunited.com/api/getAsyncLocations?template=search&level=search&search=Washington,%20DC,%20US&radius=100000&limit=100000"
    ]

    def post_process_feature(self, feature, location):
        if location["location_type_cs"] == "Branch":
            apply_category(Categories.BANK, feature)
        elif location["location_type_cs"] == "Branch & ATM":
            apply_category(Categories.BANK, feature)
            apply_yes_no(Extras.ATM, feature, True)
        elif location["location_type_cs"] == "ATM":
            apply_category(Categories.ATM, feature)
        else:
            self.logger.info("Cannot determine category, inferring location is bank")
            apply_category(Categories.BANK, feature)

        yield feature
