from locations.categories import Categories, apply_category
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class GoodlifePharmacyKESpider(AgileStoreLocatorSpider):
    name = "goodlife_pharmacy_ke"
    item_attributes = {"brand": "Goodlife Pharmacy", "brand_wikidata": "Q120783615"}
    allowed_domains = ["www.goodlife.co.ke"]

    apply_category(Categories.PHARMACY, item_attributes)
