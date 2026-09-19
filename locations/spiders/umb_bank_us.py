from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.rio_seo import RioSeoSpider

# UMB's generic ATM customer service line, shared by almost all standalone ATMs and not branch-specific.
GENERIC_ATM_PHONE = "(800) 860-4862"

LOCATION_CATEGORIES = {
    "ATM": Categories.ATM,
    "Branch": Categories.BANK,
    "Branch,Private Wealth Management": Categories.BANK,
    "Commercial Banking Center": Categories.BANK,
    "Private Wealth Management": Categories.OFFICE_FINANCIAL_ADVISOR,
}


class UmbBankUSSpider(RioSeoSpider):
    name = "umb_bank_us"
    item_attributes = {"brand": "UMB Bank", "brand_wikidata": "Q7865088"}
    end_point = "https://maps.locations.umb.com"

    def post_process_feature(self, feature, location):
        location_type = location["Location Type_CS"]
        if location_type == "ATM,Branch":
            apply_category(Categories.BANK, feature)
            apply_yes_no(Extras.ATM, feature, True)
        elif category := LOCATION_CATEGORIES.get(location_type):
            apply_category(category, feature)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unmapped_type/{location_type}")
            apply_category(Categories.BANK, feature)

        if location.get("local_phone") == GENERIC_ATM_PHONE:
            feature["phone"] = None

        yield feature
