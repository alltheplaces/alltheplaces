from locations.categories import Categories
from locations.storefinders.storepoint import StorepointSpider


class BrumbysBakeriesAUSpider(StorepointSpider):
    name = "brumbys_bakeries_au"
    item_attributes = {"brand": "Brumby's Bakeries", "brand_wikidata": "Q4978794", "extras": Categories.SHOP_BAKERY.value}
    key = "167231a6e2f944"
