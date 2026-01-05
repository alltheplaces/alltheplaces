import re
from collections import defaultdict
from enum import Enum
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.spiders.q8_italia import Q8ItaliaSpider


class GovOsservaprezziCarburantiITSpider(Spider):
    name = "gov_osservaprezzi_carburanti_it"
    dataset_attributes = {"source": "api", "api": "carburanti.mise.gov.it"}

    custom_settings = {
        "DOWNLOAD_DELAY": 0.1,
    }

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
        # sold by Eni fuel stations, is probably a premium diesel and not the adblue liquid
        "Blue Diesel": Fuel.GTL_DIESEL,
        # "Benzina" means petrol/gasoline in Italian which is always "Benzina verde", that is octane 95 petrol
        "Benzina": Fuel.OCTANE_95,
        # other values contained in source dataset sorted by number of occurrences
        "HVOlution": Fuel.BIODIESEL,
        "Blue Super": Fuel.OCTANE_100,
        "Supreme Diesel": Fuel.GTL_DIESEL,
        "HVO": Fuel.BIODIESEL,
        "Gasolio speciale": Fuel.GTL_DIESEL,
        "Gasolio Premium": Fuel.GTL_DIESEL,
        "HiQ Perform+": Fuel.OCTANE_100,
        "Benzina speciale": Fuel.OCTANE_100,
        "Benzina WR 100": Fuel.OCTANE_100,
        "GNL": Fuel.LNG,
        "L-GNC": Fuel.LNG,
        "DieselMax": Fuel.GTL_DIESEL,
        "S-Diesel": Fuel.GTL_DIESEL,
        "HVO100": Fuel.BIODIESEL,
        "Excellium Diesel": Fuel.GTL_DIESEL,
        "Benzina Shell V Power": Fuel.OCTANE_100,
        "Gasolio Oro Diesel": Fuel.GTL_DIESEL,
        "F101": Fuel.OCTANE_100,
        "REHVO": Fuel.BIODIESEL,
        "E-DIESEL": Fuel.HGV_DIESEL,
        "GP DIESEL": Fuel.GTL_DIESEL,
        "Gasolio Energy D": Fuel.HGV_DIESEL,
        "Gasolio Gelo": Fuel.COLD_WEATHER_DIESEL,
        "BCHVO": Fuel.BIODIESEL,
        "Benzina Plus 98": Fuel.OCTANE_98,
        "Diesel HVO": Fuel.BIODIESEL,
        "Gasolio HVO": Fuel.BIODIESEL,
        "Benzina Energy 98 ottani": Fuel.OCTANE_98,
        "Gasolio Bio HVO": Fuel.BIODIESEL,
        "Blu Diesel Alpino": Fuel.COLD_WEATHER_DIESEL,
        "V-Power": Fuel.OCTANE_100,
        "HVO Future": Fuel.BIODIESEL,
        "Excellium diesel": Fuel.GTL_DIESEL,
        "HVOvolution": Fuel.BIODIESEL,
        "HVO eco diesel": Fuel.BIODIESEL,
        "Gasolio Plus": Fuel.GTL_DIESEL,
        "Diesel HVO Energy": Fuel.BIODIESEL,
        "Gasolio Prestazionale": Fuel.GTL_DIESEL,
        "Verde speciale": Fuel.OCTANE_100,
        "F-101": Fuel.OCTANE_100,
        "GASOLIO HVO": Fuel.BIODIESEL,
        "Benzina Speciale 98 Ottani": Fuel.OCTANE_98,
        "Benzina 102 Ottani": Fuel.OCTANE_102,
        "Benzina 100 ottani": Fuel.OCTANE_100,
    }

    BRANDS = {
        "Api-Ip": {"brand": "IP", "brand_wikidata": "Q3788748"},
        "Esso": {"brand": "Esso", "brand_wikidata": "Q867662"},
        "Q8": Q8ItaliaSpider.item_attributes,
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
    }

    def get_price_tag(self, fuel_tag):
        if isinstance(fuel_tag, Enum):
            fuel_tag = fuel_tag.value
        return re.sub(r"^fuel:", "charge:", fuel_tag)

    async def start(self) -> AsyncIterator[JsonRequest]:
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

            fuel_prices = defaultdict(dict)
            has_self_service = False
            has_full_service = False

            # parse all types of fuel and group prices by fuel type
            for fuel in result["fuels"]:
                if fuel["name"] not in self.FUELS:
                    self.crawler.stats.inc_value(f"atp/gov_osservaprezzi_carburanti_it/unmapped_fuel/{fuel['name']}")
                    continue
                osm_fuel_tag = self.FUELS.get(fuel["name"])
                osm_fuel_price_tag = self.get_price_tag(osm_fuel_tag)

                apply_yes_no(osm_fuel_tag, item, True)

                if fuel["isSelf"]:
                    has_self_service = True
                    fuel_prices[osm_fuel_price_tag]["self_service"] = "{} EUR/1 litre".format(round(fuel["price"], 2))
                else:
                    has_full_service = True
                    fuel_prices[osm_fuel_price_tag]["full_service"] = "{} EUR/1 litre".format(round(fuel["price"], 2))

            # see https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dfuel#How_to_map
            apply_yes_no("self_service", item, has_self_service, apply_positive_only=False)
            apply_yes_no("full_service", item, has_full_service, apply_positive_only=False)

            # parse fuel prices
            for charged_fuel, prices in fuel_prices.items():
                has_one_price: bool = ("self_service" in prices) != ("full_service" in prices)
                has_identical_prices: bool = prices.get("self_service") == prices.get("full_service")
                if has_one_price or has_identical_prices:
                    # price is the same regardless of self/full service
                    item["extras"][charged_fuel] = prices[next(iter(prices))]
                else:
                    # TODO: add conditional prices for self and full service
                    # item["extras"][charged_fuel] = prices["self_service"]
                    # item["extras"][charged_fuel] = prices["full_service"]
                    self.crawler.stats.inc_value(f"atp/gov_osservaprezzi_carburanti_it/unmapped_price/{charged_fuel}")

            if (brand := result["brand"]) in self.BRANDS:
                item["name"] = None  # Use NSI name
                item.update(self.BRANDS[brand])
            elif result["brand"] == "PompeBianche":  # "brand" used by non-branded stations
                pass
            else:
                item["brand"] = item["name"] = brand  # Use the brand as the name as well
                self.crawler.stats.inc_value(f"atp/gov_osservaprezzi_carburanti_it/unmapped_brand/{brand}")
            yield item
