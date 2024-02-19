
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import point_locations


class OsservaprezziCarburantiITSpider(Spider):
    name = "osservaprezzi_carburanti_it"

    FUELS = {
        "Gasolio": Fuel.DIESEL,
        "GPL": Fuel.LPG,
        "Metano": Fuel.CNG,
        # "Blue Diesel": Fuel.ADBLUE, ?
    }

    BRANDS = {
        "Api-Ip": {"brand": "IP", "brand_wikidata": "Q646807"},
        "Esso": {"brand": "Esso", "brand_wikidata": "Q867662"},
        "Q8": {"brand": "Q8", "brand_wikidata": "Q1634762"},
        "Tamoil": {"brand": "Tamoil", "brand_wikidata": "Q706793"},
        "AgipEni": {"brand": "Eni", "brand_wikidata": "Q565594"},
        "Giap": {"brand": "Giap", "brand_wikidata": None},
        "Energas": {"brand": "Energas", "brand_wikidata": None},
        "Keropetrol": {"brand": "Keropetrol", "brand_wikidata": None},
        "San Marco Petroli": {"brand": "San Marco Petroli", "brand_wikidata": None},
    }

    def start_requests(self):
        for lat, lon in point_locations("italy_grid_10km.csv"):
            yield JsonRequest(
                "https://carburanti.mise.gov.it/ospzApi/search/zone",
                data={
                    "points": [{"lat": lat, "lng": lon}],
                    "radius": 10,
                },
            )

    def parse(self, response: Response):
        for result in response.json()["results"]:
            item = DictParser.parse(result)

            apply_category(Categories.FUEL_STATION, item)

            for fuel_name, fuel in self.FUELS.items():
                apply_yes_no(fuel, item, any(f["name"] == fuel_name for f in result["fuels"]))

            if (brand := result["brand"]) == "PompeBianche":
                # non-branded station
                yield item
            if brand in self.BRANDS:
                item.update(self.BRANDS[brand])
            else:
                item["brand"] = brand
            yield item
