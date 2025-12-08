from locations.categories import Categories, apply_category
from locations.storefinders.rio_seo import RioSeoSpider

LOCATION_CATEGORIES = {
    "ATM": Categories.ATM,
    "Branch": Categories.BANK,
    "Financial Center": Categories.OFFICE_FINANCIAL_ADVISOR,
}


class SantanderUSSpider(RioSeoSpider):
    name = "santander_us"
    item_attributes = {"brand": "Santander", "brand_wikidata": "Q5835668"}
    end_point = "https://maps.locations.santanderbank.com"

    def post_process_feature(self, feature, location):
        location_type = location["Location Type_CS"]
        category = LOCATION_CATEGORIES.get(location_type)
        if category:
            apply_category(category, feature)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_category/{location_type}")
        yield feature
