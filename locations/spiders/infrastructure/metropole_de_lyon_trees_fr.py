from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses


class MetropoleDeLyonTreesFRSpider(Spider):
    name = "metropole_de_lyon_trees_fr"
    item_attributes = {"operator": "Métropole de Lyon", "operator_wikidata": "Q16665897", "nsi_id": "N/A"}
    dataset_attributes = Licenses.ETALAB2.value | {"attribution:name": "Métropole de Lyon"}
    allowed_domains = ["data.grandlyon.com"]
    start_urls = [
        "https://data.grandlyon.com/geoserver/metropole-de-lyon/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=metropole-de-lyon:abr_arbres_alignement.abrarbre&count=10000&startIndex=0&sortBy=gid&outputFormat=application/json&srsName=EPSG:4326"
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 600}

    def parse(self, response):
        data = response.json()
        for tree in data["features"]:
            props = tree["properties"]
            # Empty planting pits and stumps are listed alongside the trees.
            if props["genre"] in ("Emplacement libre", "Souche"):
                continue
            item = Feature(
                ref=props["identifiant"],
                lon=tree["geometry"]["coordinates"][0],
                lat=tree["geometry"]["coordinates"][1],
                street=props["nomvoie"],
                city=props["commune"],
            )
            apply_category(Categories.NATURAL_TREE, item)
            item["extras"]["genus"] = props["genre"]
            if props["espece"]:
                item["extras"]["species"] = f"{props['genre']} {props['espece']}"
            item["extras"]["taxon:fr"] = props["essencefrancais"]
            item["extras"]["start_date"] = props["anneeplantation"]
            if props["hauteurtotale_m"]:
                item["extras"]["height"] = f"{props['hauteurtotale_m']} m"
            if props["circonference_cm"]:
                item["extras"]["circumference"] = f"{props['circonference_cm']} cm"
            if props["diametrecouronne_m"]:
                item["extras"]["diameter_crown"] = f"{props['diametrecouronne_m']} m"
            yield item

        for link in data.get("links", []):
            if link["rel"] == "next":
                yield response.follow(link["href"])
