import csv
from io import StringIO
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.licenses import Licenses
from locations.settings import ITEM_PIPELINES


class GovPreciosSurtidorARSpider(Spider):
    name = "gov_precios_surtidor_ar"
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "Secretaría de Energía de la Nación Argentina - Precios en Surtidor (Resolución 314/2016)",
        "attribution:website": "http://datos.energia.gob.ar/dataset/precios-en-surtidor",
        "use:commercial": "permit",
    }
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 300,
        # Multi-operator open data: count operators rather than brands.
        "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.count_operators.CountOperatorsPipeline": None},
    }
    # Argentina's Secretaría de Energía publishes every service station's current fuel
    # prices (CC-BY-4.0, commercial use permitted with attribution). The CSV has one
    # row per station x product x day/night schedule, so we group the rows of each
    # station (idempresa) into one POI and derive the fuel types it sells.
    start_urls = [
        "https://datos.energia.gob.ar/dataset/1c181390-5045-475e-94dc-410429be4b17/resource/"
        "80ac25de-a44a-4445-9215-090cf55cfda5/download/precios-en-surtidor-resolucin-3142016.csv"
    ]

    # idproducto -> OSM fuel tag. Argentine grades: "súper" (92-95 RON) is the common
    # unleaded, "premium" (>95 RON) the high-octane one; both gas-oil grades are diesel.
    FUELS = {
        "2": Fuel.OCTANE_95,  # Nafta (súper) entre 92 y 95 Ron
        "3": Fuel.OCTANE_98,  # Nafta (premium) de más de 95 Ron
        "6": Fuel.CNG,  # GNC
        "19": Fuel.DIESEL,  # Gas Oil Grado 2
        "21": Fuel.DIESEL,  # Gas Oil Grado 3 (premium diesel)
    }

    # empresabandera -> brand. Wikidata codes are the NSI fuel-brand entries. Dapsa has
    # no Wikidata item, so its name is set explicitly (NSI can't supply it); the others
    # leave name unset so NSI fills it. Flags not listed here fall through to a raw
    # brand=name mapping with an unmapped_brand stat so they can be added to NSI.
    BRANDS = {
        "YPF": {"brand": "YPF", "brand_wikidata": "Q2006989"},
        "SHELL C.A.P.S.A.": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "AXION": {"brand": "Axion", "brand_wikidata": "Q62131749"},
        "PUMA": {"brand": "Puma", "brand_wikidata": "Q7259769"},
        "GULF": {"brand": "Gulf", "brand_wikidata": "Q5617505"},
        "REFINOR": {"brand": "Refinor", "brand_wikidata": "Q10358460"},
        "DAPSA S.A.": {"brand": "Dapsa", "name": "Dapsa"},
    }

    # White-pump / unbranded independents: genuinely have no brand, so leave it unset.
    UNBRANDED = {"BLANCA", "SIN EMPRESA BANDERA"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stations: dict[str, dict] = {}
        for row in csv.DictReader(StringIO(response.text)):
            station = stations.setdefault(row["idempresa"], {"row": row, "products": set()})
            station["products"].add(row["idproducto"])

        for ref, station in stations.items():
            row = station["row"]
            item = DictParser.parse(row)  # maps latitud/longitud -> lat/lon and direccion -> addr_full
            item["ref"] = ref
            item["street_address"] = item.pop("addr_full", None)
            item["city"] = row["localidad"]
            item["state"] = row["provincia"]  # DictParser mismaps the macro-region ("region") to state
            item["operator"] = row["empresa"]

            bandera = row["empresabandera"].strip()
            if bandera in self.BRANDS:
                item["name"] = None  # use the NSI name for the brand
                item.update(self.BRANDS[bandera])
            elif bandera in self.UNBRANDED:
                pass  # white-pump independents genuinely have no brand
            else:
                item["brand"] = item["name"] = bandera  # keep the raw flag until it is added to NSI
                self.crawler.stats.inc_value("atp/{}/unmapped_brand/{}".format(self.name, bandera))

            apply_category(Categories.FUEL_STATION, item)
            for product in station["products"]:
                if fuel := self.FUELS.get(product):
                    apply_yes_no(fuel, item, True)
                else:
                    self.crawler.stats.inc_value("atp/{}/unmapped_product/{}".format(self.name, product))
            yield item
