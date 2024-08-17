from locations.categories import Categories
from locations.storefinders.rio_seo import RioSeoSpider


class StaplesCASpider(RioSeoSpider):
    name = "staples_ca"
    item_attributes = {"brand": "Staples", "brand_wikidata": "Q17149420", "extras": Categories.SHOP_STATIONERY.value}
    end_point = "https://maps.stores.staples.ca"
