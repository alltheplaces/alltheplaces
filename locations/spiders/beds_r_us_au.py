from locations.categories import Categories
from locations.storefinders.storemapper import StoremapperSpider


class BedsRUSAUSpider(StoremapperSpider):
    name = "beds_r_us_au"
    item_attributes = {"brand": "Beds R Us", "brand_wikidata": "Q126179491", "extras": Categories.SHOP_BED.value}
    company_id = "27289-rJ0a0kvXQGRyNCLs"
