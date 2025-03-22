import pyproj
import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class NotfalltreffpunkteCHSpider(scrapy.Spider):
    name = "notfalltreffpunkte_ch"
    allowed_domains = ["data.geo.admin.ch"]
    dataset_attributes = {
        "attribution": "optional",
        "attribution:name:de": "Schweizer Bundesamt für Bevölkerungsschutz",
        "attribution:name:en": "Swiss Federal Office for Civil Protection",
        "attribution:wikidata": "Q3349626",
        "license": "opendata.swiss OPEN",
        "license:website": "https://www.geocat.ch/geonetwork/srv/eng/catalog.search#/metadata/ed3039e3-6437-4be9-8c99-a3111da201ab",
        "license:wikidata": "Q133462062",
    }

    # Swiss LV95 (https://epsg.io/2056) -> lat/lon (https://epsg.io/4326)
    coord_transformer = pyproj.Transformer.from_crs(2056, 4326)

    def start_requests(self):
        yield scrapy.Request(
            "https://data.geo.admin.ch/ch.babs.notfalltreffpunkte/notfalltreffpunkte/notfalltreffpunkte.geojson",
        )

    def parse(self, response):
        for f in response.json()["features"]:
            props = f["properties"]
            coords = f["geometry"].get("coordinates", [])
            if len(coords) < 2:
                continue
            lat, lon = self.coord_transformer.transform(coords[0], coords[1])
            item = {
                "ref": props.get("ntp-id"),
                "lat": lat,
                "lon": lon,
                "name": props.get("gebbezeichnung"),
                "street": props.get("strasse"),
                "housenumber": props.get("nummer"),
                "postcode": str(props.get("plz")),
                "city": props.get("gemeinde"),
                "country": "CH",
            }
            apply_category(Categories.DISASTER_HELP_POINT, item)
            yield Feature(**item)
