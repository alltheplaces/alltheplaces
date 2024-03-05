import logging

import pyproj
import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


# Open Data of the City of Winterthur, Switzerland
class WinterthurCHSpider(scrapy.Spider):
    name = "winterthur_ch"
    allowed_domains = ["stadtplan.winterthur.ch"]
    dataset_attributes = {
        "attribution": "optional",
        "attribution:name:de": "Stadt Winterthur",
        "attribution:name:en": "City of Winterthur",
        "attribution:wikidata": "Q9125",
        "license": "Creative Commons Zero",
        "license:website": "https://stadtplan.winterthur.ch/stadtgruen/spielplatzkontrolle-service/swagger/index.html",
        "license:wikidata": "Q6938433",
    }
    no_refs = True

    # Swiss LV95 (https://epsg.io/2056) -> lat/lon (https://epsg.io/4326)
    coord_transformer = pyproj.Transformer.from_crs(2056, 4326)

    def start_requests(self):
        yield scrapy.Request(
            "https://stadtplan.winterthur.ch/stadtgruen/spielplatzkontrolle-service/Collections/Playgrounds/Items/",
            callback=self.parse_playgrounds,
        )
        yield scrapy.Request(
            "https://stadtplan.winterthur.ch/wfs/SitzbankWfs?service=wfs"
            + "&version=2.0.0&request=GetFeature&format=json"
            + "&typeNames=ms:SitzbankWfs",
            callback=self.parse_benches,
        )

    def parse_playgrounds(self, response):
        abbrevs = {
            "KG": "Kindergarten",
            "SH": "Schulhaus",
        }
        for f in response.json():
            props = f["properties"]
            coords = f["geometry"].get("coordinates", [])
            if len(coords) < 2:
                continue
            lat, lon = self.coord_transformer.transform(coords[0], coords[1])
            item = {
                "lat": lat,
                "lon": lon,
                "street": props.get("streetName"),
                "housenumber": props.get("houseNo"),
                "city": "Winterthur",
                "country": "CH",
                "operator": "Stadtgrün Winterthur",
                "operator_wikidata": "Q56825906",
            }
            apply_category(Categories.LEISURE_PLAYGROUND, item)
            if name_words := props.get("name", "").split():
                name_words[0] = abbrevs.get(name_words[0], name_words[0])
                item["name"] = " ".join(name_words)
            ref_emergency = props.get("nummer")
            if ref_emergency and ref_emergency > 0:
                item["extras"]["ref:emergency"] = str(ref_emergency)
            yield Feature(**item)

    def parse_benches(self, response):
        for m in response.json()["FeatureCollection"]["member"]:
            if f := m.get("SitzbankWfs"):
                coords = f["msGeometry"]["Point"]["pos"].split()
                [x, y] = [float(c) for c in coords[:2]]
                lat, lon = self.coord_transformer.transform(x, y)
                btype = (f.get("Banktyp") or "").strip()
                item = {
                    "lat": lat,
                    "lon": lon,
                    "city": "Winterthur",
                    "country": "CH",
                    "operator": "Stadtgrün Winterthur",
                    "operator_wikidata": "Q56825906",
                    "extras": {
                        "backrest": self.parse_bench_backrest(btype),
                        "colour": self.parse_bench_colour(btype),
                        "inscription": self.parse_bench_inscription(f),
                        "material": self.parse_bench_material(btype),
                        "material:wikidata": self.parse_bench_material_wikidata(btype),
                    },
                    "ref": f["Banknummer"],
                }
                apply_category(Categories.BENCH, item)
                yield Feature(**item)

    def parse_bench_backrest(self, btype):
        backrests = {
            "Eichenbank mit Lehne": "yes",
            "Eichenbank ohne Lehne": "no",
            "Eichenbank Halbling": "no",
            "Eichenbank Spezial": "no",
            "Eichenbank Tisch/Bank": "no",
            "Sitzbank braun": "yes",
            "Sitzbank grau": "yes",
            "Sitzbank rot": "yes",
            "Sitzbank Eiche": "yes",
            "Standardbank Latten braun": "yes",
            "Standardbank Latten grau": "yes",
            "Standardbank Latten rot": "yes",
            "undefiniert": None,
            "": None,
        }
        if btype in backrests:
            return backrests[btype]
        logging.error(f'cannot determine backrest for "{btype}"')
        return None

    def parse_bench_colour(self, btype):
        # RGB values according to photographs of benches in Winterthur.
        colours = {
            "braun": "#DDBB88",
            "eichenbank": "#DDBB88",
            "eiche": "#DDBB88",
            "grau": "#AABBDD",
            "rot": "#FF6633",
        }
        for word in btype.lower().split():
            if col := colours.get(word):
                return col
        if btype not in {"", "undefiniert"}:
            logging.error(f'cannot determine color for "{btype}"')
        return None

    def parse_bench_material(self, btype):
        for word in btype.split():
            if word in {"Eiche", "Eichenbank", "Latten"}:
                return "wood"
        return None

    def parse_bench_material_wikidata(self, btype):
        for word in btype.split():
            if word in {"Eiche", "Eichenbank"}:
                return "Q33036816"
        return None

    def parse_bench_inscription(self, f):
        if ins := (f.get("Widmung") or "").strip():
            return ins
        else:
            return None
