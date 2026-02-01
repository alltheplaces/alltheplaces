from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.spiders.albertsons import AlbertsonsSpider
from locations.spiders.cvs_us import PHARMACY_BRANDS as CVS_BRANDS
from locations.spiders.market_basket_us import MarketBasketUSSpider
from locations.spiders.shoprite_us import ShopriteUSSpider
from locations.spiders.target_us import TargetUSSpider
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

    LOCATED_IN_MAPPINGS = [
        (["CVS STORE", "CVS PHARMACY"], CVS_BRANDS["CVS Pharmacy"]),
        (["TARGET"], TargetUSSpider.item_attributes),
        (["DEMOULAS MARKET BASKET", "MARKET BASKET"], MarketBasketUSSpider.item_attributes),
        (["SHAW'S SUPERMARKET", "SHAWS"], AlbertsonsSpider.brands["shaws"]),
        (["SHOPRITE"], ShopriteUSSpider.item_attributes),
    ]

    def post_process_feature(self, feature, location):
        location_type = location["Location Type_CS"]
        category = LOCATION_CATEGORIES.get(location_type)
        if category:
            apply_category(category, feature)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_category/{location_type}")

        if category == Categories.ATM and feature.get("name"):
            feature["located_in"], feature["located_in_wikidata"] = extract_located_in(
                feature["name"], self.LOCATED_IN_MAPPINGS, self
            )

        yield feature
