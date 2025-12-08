import hashlib
import io
import json
import zipfile
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, Vending, add_vending, apply_category, apply_yes_no
from locations.items import Feature


# Open Data of the Land Surveying Office of the City of Bern, Switzerland
# https://opendata.swiss/en/organization/geoinformation-der-stadt-bern
# https://opendata.swiss/en/dataset/velo-themen
class BernCHSpider(Spider):
    name = "bern_ch"
    allowed_domains = ["map.bern.ch"]

    dataset_attributes = {
        "attribution": "required",
        "attribution:name:de": "Geodaten Stadt Bern",
        "attribution:name:en": "Geodata City of Bern",
        "attribution:website": "https://www.bern.ch/themen/planen-und-bauen/geodaten-und-plane",
        "contact:email": "geoinformation@bern.ch",
        "license": "opendata.swiss BY-ASK",
        "license:website": "https://opendata.swiss/de/terms-of-use#terms_by_ask",
        "license:wikidata": "Q115716001",
        "use:commercial": "permit",
        # permission for import to OpenStreetMap has been granted, 2022-12-22
        "use:openstreetmap": "yes",
        "website": "https://opendata.swiss/de/dataset/velo-themen",
    }

    operators = {
        "carvelo2go": ("Q110278232", {"rental": "cargo_bike"}),
        "PubliBike": ("Q3555363", {}),
        "Rent a Bike": ("Q115701374", {}),
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://map.bern.ch/ogd/poi_velo/poi_velo_json.zip", callback=self.parse_bicycle_zipfile)

    def parse_bicycle_zipfile(self, response):
        with zipfile.ZipFile(io.BytesIO(response.body)) as feed_zip:
            with feed_zip.open("poi_velo_wgs84.json") as feed_file:
                feed_json = json.load(feed_file)
        parsers = {
            "Schlauchautomat": self.parse_bicycle_tube_vending_machine,
            "Veloabstellplatz": self.parse_bicycle_parking,
            "Velofachgeschaeft": self.parse_bicycle_shop,
            "Velomiete": self.parse_bicycle_rental,
            "Velopumpe": self.parse_bicycle_pump,
            "Velostrasse": self.parse_bicycle_road,
        }
        for collection in feed_json:
            for feature in collection["features"]:
                type = feature.get("properties", {}).get("rubrik")
                if type not in parsers:
                    self.logger.error('unknown category: "%s"' % type)
                    continue
                if item := parsers[type](feature):
                    yield item

    def parse_feature(self, f):
        props = f["properties"]
        feature_json = json.dumps(f, sort_keys=True)
        ref = hashlib.sha1(feature_json.encode("utf-8")).hexdigest()
        return {
            "geometry": f["geometry"],
            "ref": ref,
            "street": props.get("strasse"),
            "housenumber": props.get("hausnummer"),
            "postcode": props.get("plz"),
            "city": props.get("ort"),
            "country": "CH",
            "extras": {},
        }

    def parse_bicycle_parking(self, f):
        item = self.parse_feature(f)
        apply_category(Categories.BICYCLE_PARKING, item)
        return Feature(**item)

    def parse_bicycle_pump(self, f):
        item = self.parse_feature(f)
        apply_category(Categories.COMPRESSED_AIR, item)
        item["extras"].update(
            {
                "fee": "no",
                "pressure": "8",
                "valves": "schrader;sclaverand",
            }
        )
        return Feature(**item)

    def parse_bicycle_rental(self, f):
        item, props = self.parse_feature(f), f["properties"]
        if operator := props.get("punktname"):
            operator_wikidata, extras = self.operators.get(operator, (None, {}))
            item["operator"] = operator
            item["operator_wikidata"] = operator_wikidata
            item["extras"].update(
                {
                    "operator:phone": props.get("telefon"),
                }
            )
            item["extras"].update(extras)
        apply_category(Categories.BICYCLE_RENTAL, item)
        return Feature(**item)

    def parse_bicycle_road(self, f):
        item = self.parse_feature(f)
        apply_category(Categories.HIGHWAY_RESIDENTIAL, item)
        apply_yes_no("bicycle_road", item, True)
        return item

    def parse_bicycle_shop(self, f):
        item, props = self.parse_feature(f), f["properties"]
        item.update(
            {
                "name": props.get("punktname"),
                "email": props.get("email"),
                "phone": props.get("telefon"),
                "website": props.get("url"),
            }
        )
        apply_category(Categories.SHOP_BICYCLE, item)
        return Feature(**item)

    def parse_bicycle_tube_vending_machine(self, f):
        item, props = self.parse_feature(f), f["properties"]
        item["operator"] = props.get("punktname")
        item["extras"].update(
            {
                "operator:email": props.get("email"),
                "operator:phone": props.get("telefon"),
                "operator:website": props.get("url"),
            }
        )
        apply_category(Categories.VENDING_MACHINE, item)
        add_vending(Vending.BICYCLE_TUBE, item)
        return Feature(**item)
