from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import point_locations


class GovOsservaprezziCarburantiITSpider(Spider):
    name = "gov_osservaprezzi_carburanti_it"

    FUELS = {
        "GPL": Fuel.LPG,
        "Metano": Fuel.CNG,
        "Gasolio": Fuel.DIESEL,
        "Gasolio Ecoplus": Fuel.BIODIESEL,
        "Gasolio Artico": Fuel.COLD_WEATHER_DIESEL,
        "Gasolio artico": Fuel.COLD_WEATHER_DIESEL,
        "Gasolio Artico Igloo": Fuel.COLD_WEATHER_DIESEL,
        "Gasolio Alpino": Fuel.COLD_WEATHER_DIESEL,
        "V-Power Diesel": Fuel.GTL_DIESEL,
        "Hi-Q Diesel": Fuel.GTL_DIESEL,
        "Diesel Shell V Power": Fuel.GTL_DIESEL,
        # no official tag
        "Benzina": "fuel:petrol",
    }

    BRANDS = {
        "Api-Ip": {"brand": "IP", "brand_wikidata": "Q646807"},
        "Esso": {"brand": "Esso", "brand_wikidata": "Q867662"},
        "Q8": {"brand": "Q8", "brand_wikidata": "Q1634762"},
        "Tamoil": {"brand": "Tamoil", "brand_wikidata": "Q706793"},
        "AgipEni": {"brand": "Eni", "brand_wikidata": "Q565594"},
        "Shell": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "Europam": {"brand": "Europam", "brand_wikidata": "Q115268198"},
        "Giap": {"brand": "Giap", "brand_wikidata": "Q107609037"},
        "Energas": {"brand": "Energas", "brand_wikidata": "Q124623439"},
        "KEROPETROL": {"brand": "Keropetrol", "brand_wikidata": "Q124336939"},
        "SanMarcoPetroli": {"brand": "San Marco Petroli", "brand_wikidata": "Q124623464"},
        "Retitalia": {"brand": "Retitalia", "brand_wikidata": "Q119135752"},
        "Beyfin": {"brand": "Beyfin", "brand_wikidata": "Q3639256"},
        "Costantin": {"brand": "Costantin", "brand_wikidata": "Q48800790"},
        "Lukoil": {"brand": "Lukoil", "brand_wikidata": "Q329347"},
        # "brand" used by non-branded stations
        "PompeBianche": {},
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

            for fuel in result["fuels"]:
                if fuel["name"] not in self.FUELS:
                    self.crawler.stats.inc_value(f"atp/gov_osservaprezzi_carburanti_it/unmapped_fuel/{fuel['name']}")
                apply_yes_no(self.FUELS.get(fuel["name"]), item, fuel["name"] in self.FUELS)

            if (brand := result["brand"]) in self.BRANDS:
                item.update(self.BRANDS[brand])
            else:
                item["brand"] = brand
                self.crawler.stats.inc_value(f"atp/gov_osservaprezzi_carburanti_it/unmapped_brand/{brand}")
            yield item
