import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import point_locations


class ColesAUSpider(scrapy.Spider):
    name = "coles_au"

    BRANDS = {
        1: {"brand": "Coles Express", "brand_wikidata": "Q5144653", "extras": Categories.SHOP_CONVENIENCE.value},
        2: {"brand": "Coles Supermarkets", "brand_wikidata": "Q1108172"},
        3: {"brand": "Liquorland", "brand_wikidata": "Q2283837"},
        4: {"brand": "1st Choice", "brand_wikidata": "Q4596269"},  # AKA First Choice Liquor
        5: {"brand": "Vintage Cellars", "brand_wikidata": "Q7932815"},
    }

    def start_requests(self):
        for lat, lon in point_locations("au_centroids_20km_radius.csv"):
            yield JsonRequest(
                f"https://apigw.coles.com.au/digital/colesweb/v1/stores/search?latitude={lat}&longitude={lon}&brandIds=1,2,3,4,5&numberOfStores=15",
            )

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)

            if brand := self.BRANDS.get(location["brandId"]):
                item.update(brand)
            else:
                item["brand"] = location["brandName"]

            # TODO: tradingHours

            yield item
