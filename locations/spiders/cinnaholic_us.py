from locations.categories import Categories
from locations.storefinders.where2getit import Where2GetItSpider


class CinnaholicUSSpider(Where2GetItSpider):
    name = "cinnaholic_us"
    item_attributes = {"brand": "Cinnaholic", "brand_wikidata": "Q48965480", "extras": Categories.SHOP_BAKERY.value}
    api_key = "E54F429C-E8DC-11ED-A099-3DDBD7DDC1D0"
