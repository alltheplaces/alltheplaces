from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class BordeauxMetropoleTreesFRSpider(OpendatasoftExploreSpider):
    name = "bordeaux_metropole_trees_fr"
    item_attributes = {"operator": "Bordeaux Métropole", "operator_wikidata": "Q1117116", "nsi_id": "N/A"}
    dataset_attributes = OpendatasoftExploreSpider.dataset_attributes | {
        "license": "Licence Ouverte 1.0",
        "license:website": "https://www.etalab.gouv.fr/wp-content/uploads/2014/05/Licence_Ouverte.pdf",
        "license:wikidata": "Q80938815",
        "attribution": "required",
        "attribution:name": "Bordeaux Métropole",
    }
    api_endpoint = "https://opendata.bordeaux-metropole.fr/api/explore/v2.1/"
    dataset_id = "ec_arbre_p"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature["statut"] != "VIVANT":
            return
        item["ref"] = str(feature["gid"])
        item["city"] = feature["nom"]
        apply_category(Categories.NATURAL_TREE, item)
        if feature["espece"] != "Indéterminé":
            item["extras"]["genus"] = feature["espece"].split(" ")[0]
            if not feature["espece"].endswith(" sp."):
                item["extras"]["species"] = feature["espece"]
            item["extras"]["taxon:fr"] = feature["nom_francais"]
        item["extras"]["leaf_type"] = "needleleaved" if feature["classe"] == "Conifère" else "broadleaved"
        if feature["hauteur"]:
            item["extras"]["height"] = f"{feature['hauteur']} m"
        if feature["circonference_tronc"]:
            item["extras"]["circumference"] = f"{feature['circonference_tronc']:g} cm"
        if feature["diametre_tronc"]:
            item["extras"]["diameter"] = f"{feature['diametre_tronc']:g} cm"
        if feature["diametre_couronne"]:
            item["extras"]["diameter_crown"] = f"{feature['diametre_couronne']} m"
        if feature["date_plantation"]:
            item["extras"]["start_date"] = feature["date_plantation"]
        yield item
