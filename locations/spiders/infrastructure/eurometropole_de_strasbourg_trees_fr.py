from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class EurometropoleDeStrasbourgTreesFRSpider(OpendatasoftExploreSpider):
    name = "eurometropole_de_strasbourg_trees_fr"
    item_attributes = {"operator": "Eurométropole de Strasbourg", "operator_wikidata": "Q586704", "nsi_id": "N/A"}
    dataset_attributes = (
        OpendatasoftExploreSpider.dataset_attributes
        | Licenses.ETALAB2.value
        | {"attribution:name": "Ville et eurométropole de Strasbourg"}
    )
    api_endpoint = "https://data.strasbourg.eu/api/explore/v2.1/"
    dataset_id = "patrimoine_arbore"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["num_arbre"]
        apply_category(Categories.NATURAL_TREE, item)
        if feature["genre"] and feature["genre"] != "Essence":
            item["extras"]["genus"] = feature["genre"]
            if species := self.parse_species(feature["si_essence"]):
                item["extras"]["species"] = species
            if feature["si_essence"] != species:
                item["extras"]["taxon"] = feature["si_essence"]
        if feature["si_hauteur"] not in (None, "", "0"):
            item["extras"]["height"] = f"{feature['si_hauteur']} m"
        if feature["si_largeur_couronne"] not in (None, "", "0"):
            item["extras"]["diameter_crown"] = f"{feature['si_largeur_couronne']} m"
        if feature["si_diametre_fut"] not in (None, "", "0"):
            item["extras"]["diameter"] = f"{feature['si_diametre_fut']} cm"
        yield item

    @staticmethod
    def parse_species(essence: str) -> str | None:
        # "Platanus acerifolia x" is a hybrid, "Tilia cordata Green Spire" a cultivar.
        words = essence.replace(" - ", " ").replace("ï", "i").split()
        if len(words) < 2 or not words[1].isalpha() or not words[1].islower() or words[1] in ("sp", "ssp"):
            return None
        if len(words) > 2 and words[2] == "x":
            return f"{words[0]} × {words[1]}"
        return f"{words[0]} {words[1]}"
