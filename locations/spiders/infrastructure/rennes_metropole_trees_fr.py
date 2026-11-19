from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class RennesMetropoleTreesFRSpider(OpendatasoftExploreSpider):
    name = "rennes_metropole_trees_fr"
    item_attributes = {"nsi_id": "N/A"}
    dataset_attributes = OpendatasoftExploreSpider.dataset_attributes | {
        "license": "Open Database License",
        "license:website": "https://opendatacommons.org/licenses/odbl/",
        "license:wikidata": "Q1224853",
        "attribution": "required",
        "attribution:name": "Rennes Métropole",
    }
    api_endpoint = "https://data.rennesmetropole.fr/api/explore/v2.1/"
    dataset_id = "arbre"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature["abattu"] == 1:
            return
        item["addr_full"] = feature["localisation"]
        apply_category(Categories.NATURAL_TREE, item)
        if feature["genre"] != "Non renseigné":
            item["extras"]["genus"] = feature["genre"]
            if feature["espece"] and feature["espece"] not in ("sp", "sp."):
                item["extras"]["species"] = f"{feature['genre']} {feature['espece']}"
        if feature["nom_commun"] != "Non renseigné":
            item["extras"]["taxon:fr"] = feature["nom_commun"]
        if feature["hauteur"]:
            item["extras"]["height"] = f"{feature['hauteur']:g} m"
        if feature["circonference"]:
            item["extras"]["circumference"] = f"{feature['circonference']:g} cm"
        yield item
