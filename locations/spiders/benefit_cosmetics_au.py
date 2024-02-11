from locations.categories import Categories
from locations.storefinders.metalocator import MetaLocatorSpider


class BenefitCosmeticsAUSpider(MetaLocatorSpider):
    name = "benefit_cosmetics_au"
    item_attributes = {"brand_wikidata": "Q2895769", "brand": "Benefit", "extras": Categories.SHOP_BEAUTY.value}
    brand_id = "17147"
    country_list = ["Australia"]