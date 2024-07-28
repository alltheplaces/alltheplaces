from locations.categories import Categories, apply_category
from locations.storefinders.metalocator import MetaLocatorSpider


class BettsAUSpider(MetaLocatorSpider):
    name = "betts_au"
    item_attributes = {"brand": "Betts", "brand_wikidata": "Q118555401"}
    brand_id = "6176"

    apply_category(Categories.SHOP_SHOES, item_attributes)
