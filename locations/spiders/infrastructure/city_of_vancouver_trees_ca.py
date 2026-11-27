from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class CityOfVancouverTreesCASpider(OpendatasoftExploreSpider):
    name = "city_of_vancouver_trees_ca"
    item_attributes = {"operator": "City of Vancouver", "operator_wikidata": "Q24639", "nsi_id": "N/A"}
    dataset_attributes = OpendatasoftExploreSpider.dataset_attributes | {
        "license": "Open Government Licence – Vancouver",
        "license:website": "https://opendata.vancouver.ca/pages/licence/",
        "attribution": "required",
        "attribution:name": "Contains information licensed under the Open Government Licence – Vancouver.",
    }
    api_endpoint = "https://opendata.vancouver.ca/api/explore/v2.1/"
    dataset_id = "public-trees"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["asset_id"])
        apply_category(Categories.NATURAL_TREE, item)
        if feature["genus_name"]:
            genus = feature["genus_name"].title()
            item["extras"]["genus"] = genus
            if feature["species_name"] not in ("SPECIES", "XX"):
                epithet = " ".join(feature["species_name"].lower().split())
                # Hybrids are written as "FREEMANII   X"
                if epithet.endswith(" x"):
                    epithet = "x " + epithet.removesuffix(" x")
                item["extras"]["species"] = f"{genus} {epithet}"
            item["extras"]["taxon:en"] = feature["common_name"].title()
        if feature["height_m"]:
            item["extras"]["height"] = f"{feature['height_m']} m"
        if feature["diameter_cm"]:
            item["extras"]["diameter"] = f"{feature['diameter_cm']} cm"
        yield item
