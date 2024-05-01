from scrapy import Selector, Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.google_url import url_to_coords


class SuperDelNorteMXSpider(Spider):
    name = "super_del_norte_mx"
    item_attributes = {
        "brand": "Super del Norte",
        "brand_wikidata": "Q88388513",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["superdelnorte.com.mx"]
    start_urls = ["https://superdelnorte.com.mx/api/tiendas"]

    def parse(self, response):
        for location in response.json()["result"]:
            item = DictParser.parse(location)
            item["street_address"] = location["descrp"].strip()
            google_maps_url = Selector(text=location["map"]).xpath("//iframe/@src").get()
            item["lat"], item["lon"] = url_to_coords(google_maps_url)
            yield item
