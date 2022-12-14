import hashlib
import io
import json
import zipfile

import scrapy

from locations.categories import Categories, apply_category
from locations.items import GeojsonPointItem


# Open Data of the Land Surveying Office of the City of Bern, Switzerland
# https://opendata.swiss/en/organization/geoinformation-der-stadt-bern
# https://opendata.swiss/en/dataset/velo-themen
class BernCHSpider(scrapy.Spider):
    name = "bern_ch"
    allowed_domains = ["map.bern.ch"]
    operators = {
        "carvelo2go": ("Q110278232", {"rental": "cargo_bike"}),
        "PubliBike": ("Q3555363", {}),
        "Rent a Bike": ("Q115701374", {}),
    }

    def start_requests(self):
        yield scrapy.Request("https://map.bern.ch/ogd/poi_velo/poi_velo_json.zip", callback=self.parse_bicycle_zipfile)

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
        (lon, lat), props = f["geometry"]["coordinates"][:2], f["properties"]
        feature_json = json.dumps(f, sort_keys=True)
        ref = hashlib.sha1(feature_json.encode("utf-8")).hexdigest()
        return {
            "lat": lat,
            "lon": lon,
            "ref": ref,
            "street": props["strasse"],
            "housenumber": props.get("hausnummer"),
            "postcode": props.get("plz"),
            "city": props.get("ort"),
            "country": "CH",
            "extras": {},
        }

    def parse_bicycle_parking(self, f):
        item = self.parse_feature(f)
        apply_category(Categories.BICYCLE_PARKING, item)
        return GeojsonPointItem(**item)

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
        return GeojsonPointItem(**item)

    def parse_bicycle_rental(self, f):
        item, props = self.parse_feature(f), f["properties"]
        if operator := props.get("punktname"):
            operator_wikidata, extras = self.operators.get(operator, (None, {}))
            item["extras"].update(
                {
                    "operator": operator,
                    "operator:phone": props.get("telefon"),
                    "operator:wikidata": operator_wikidata,
                }
            )
            item["extras"].update(extras)
        apply_category(Categories.BICYCLE_RENTAL, item)
        return GeojsonPointItem(**item)

    def parse_bicycle_road(self, f):
        # Not emitting road geometry until AllThePlaces has made a decision
        # on whether this kind of GIS data should be considered in scope.
        # See also https://github.com/alltheplaces/alltheplaces/pull/4298.
        return None

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
        return GeojsonPointItem(**item)

    def parse_bicycle_tube_vending_machine(self, f):
        item, props = self.parse_feature(f), f["properties"]
        item["extras"].update(
            {
                "operator": props.get("punktname"),
                "operator:email": props.get("email"),
                "operator:phone": props.get("telefon"),
                "operator:website": props.get("url"),
            }
        )
        apply_category(Categories.VENDING_MACHINE_BICYCLE_TUBE, item)
        return GeojsonPointItem(**item)
