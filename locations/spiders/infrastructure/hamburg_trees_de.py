from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class HamburgTreesDESpider(Spider):
    name = "hamburg_trees_de"
    item_attributes = {"operator": "Freie und Hansestadt Hamburg", "operator_wikidata": "Q1055", "nsi_id": "N/A"}
    dataset_attributes = {
        "license": "Data licence Germany – attribution – version 2.0",
        "license:website": "https://www.govdata.de/dl-de/by-2-0",
        "license:wikidata": "Q64859812",
        "attribution": "required",
        "attribution:name": "Freie und Hansestadt Hamburg, Behörde für Umwelt, Klima, Energie und Agrarwirtschaft",
    }
    allowed_domains = ["api.hamburg.de"]
    start_urls = [
        "https://api.hamburg.de/datasets/v1/strassenbaumkataster/collections/strassenbaumkataster_hh/items?f=json&limit=10000&crs=http://www.opengis.net/def/crs/OGC/1.3/CRS84"
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 300}

    def parse(self, response):
        data = response.json()
        for tree in data["features"]:
            props = tree["properties"]
            lon, lat = tree["geometry"]["coordinates"][0]
            item = Feature(
                ref=str(props["baumid"]),
                lat=lat,
                lon=lon,
                street=props.get("strasse"),
                city="Hamburg",
            )
            if props.get("hausnummer", "0") != "0":
                item["housenumber"] = props["hausnummer"]
            apply_category(Categories.NATURAL_TREE, item)
            item["extras"]["genus"] = props.get("gattung_latein")
            species = props.get("art_latein", "")
            if " " in species and not species.endswith(" spec."):
                item["extras"]["species"] = species
            item["extras"]["taxon:de"] = props.get("art_deutsch")
            if props.get("pflanzjahr"):
                item["extras"]["start_date"] = str(props["pflanzjahr"])
            if props.get("stammumfang"):
                item["extras"]["circumference"] = f"{props['stammumfang']} cm"
            if props.get("kronendurchmesser"):
                item["extras"]["diameter_crown"] = f"{props['kronendurchmesser']} m"
            yield item

        for link in data["links"]:
            if link["rel"] == "next":
                yield response.follow(link["href"])
