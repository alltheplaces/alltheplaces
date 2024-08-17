from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.rio_seo import RioSeoSpider


class CommerceBankUSSpider(RioSeoSpider):
    name = "commerce_bank_us"
    item_attributes = {"brand": "Commerce Bank", "brand_wikidata": "Q5152411"}
    end_point = "https://maps.locations.commercebank.com"

    def post_process_feature(self, feature, location):
        if location["Location Type_CS"] == "ATM":
            apply_category(Categories.ATM, feature)
        elif location["Location Type_CS"] == "Branch":
            apply_category(Categories.BANK, feature)
        elif location["Location Type_CS"] == "Branch,ATM":
            apply_category(Categories.BANK, feature)
            apply_yes_no(Extras.ATM, feature, True)
        elif location["Location Type_CS"] == "Financial Center":
            apply_category(Categories.OFFICE_FINANCIAL, feature)

        yield feature
