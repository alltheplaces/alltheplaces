from locations.spiders.la_comer_mx import LaComerMXSpider


class CityMarketMXSpider(LaComerMXSpider):
    name = "city_market_mx"
    item_attributes = {"brand": "City Market", "brand_wikidata": "Q65090778"}
    locations_key = ["listCity"]
