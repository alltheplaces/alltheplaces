from locations.categories import Categories
from locations.storefinders.yext import YextSpider


class ArcaplanetITSpider(YextSpider):
    name = "arcaplanet_it"
    item_attributes = {"brand": "Arcaplanet", "brand_wikidata": "Q105530937", "extras": Categories.SHOP_PET.value}
    api_key = "e0faf99fdcbc6c43da0eaf74c90c23d1"
    api_version = "20220511"
