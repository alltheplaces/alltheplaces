from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class VilleDeParisTreesFRSpider(OpendatasoftExploreSpider):
    name = "ville_de_paris_trees_fr"
    item_attributes = {"operator": "Ville de Paris", "operator_wikidata": "Q90", "nsi_id": "N/A"}
    dataset_attributes = OpendatasoftExploreSpider.dataset_attributes | {
        "license": "Open Database License",
        "license:website": "https://opendatacommons.org/licenses/odbl/",
        "license:wikidata": "Q1224853",
        "attribution": "required",
        "attribution:name": "Ville de Paris",
    }
    api_endpoint = "https://opendata.paris.fr/api/explore/v2.1/"
    dataset_id = "les-arbres"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["idbase"])
        item["street_address"] = feature["adresse"]
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["genus"] = feature["genre"]
        if feature["espece"] and not feature["espece"].endswith("sp."):
            item["extras"]["species"] = f"{feature['genre']} {feature['espece']}"
        item["extras"]["taxon:fr"] = feature["libellefrancais"]
        if feature["hauteurenm"]:
            item["extras"]["height"] = f"{feature['hauteurenm']} m"
        if feature["circonferenceencm"]:
            item["extras"]["circumference"] = f"{feature['circonferenceencm']} cm"
        yield item
