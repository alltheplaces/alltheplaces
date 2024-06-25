from itertools import chain

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class MetrorowerPLSpider(Spider):
    name = "metrorower_pl"
    item_attributes = {
        "brand": "Metrorower",
        "brand_wikidata": "Q123507620",
        "extras": {"network": "Metrorower", "network:wikidata": "Q123507620", "bicycle_rental": "dropoff_point"},
    }
    start_urls = ["https://api-gateway.nextbike.pl/api/maps/service/zz/locations"]

    def parse(self, response):
        places = list(chain.from_iterable([x["places"] for x in response.json()[0]["cities"]]))
        stations = [z for z in places if z["number"] != 0]  # filter out bikes outside the stations
        for station in stations:
            item = Feature()

            item["lon"], item["lat"] = station["geoCoords"]["lng"], station["geoCoords"]["lat"]
            item["ref"] = station["number"]
            apply_category(Categories.BICYCLE_RENTAL, item)
            yield item
