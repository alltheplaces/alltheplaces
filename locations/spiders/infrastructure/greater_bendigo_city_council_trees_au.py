from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.vector_file_spider import VectorFileSpider


class GreaterBendigoCityCouncilTreesAUSpider(VectorFileSpider):
    name = "greater_bendigo_city_council_trees_au"
    item_attributes = {"operator": "Greater Bendigo City Council", "operator_wikidata": "Q134285890", "state": "VIC"}
    allowed_domains = ["data.gov.au"]
    start_urls = [
        "https://data.gov.au/data/dataset/d17c9e50-fab1-40e6-b91d-6e665faf2656/resource/b3f01081-924c-41b7-989a-cf521ca136ea/download/cogb-environment-trees.shz"
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["AssetID"]
        item["housenumber"] = feature["House"]
        item["street"] = feature["St_Name"]
        item["city"] = feature["Suburb"]
        apply_category(Categories.NATURAL_TREE, item)
        if feature["Species"] and feature["Species"] != "Not Specified":
            species = feature["Species"]
            if " - " in species:
                item["extras"]["species"] = species.split(" - ", 1)[0]
                item["extras"]["taxon:en"] = species.split(" - ", 1)[1]
            elif " (" in species and species.endswith(")"):
                item["extras"]["species"] = species.split(" (", 1)[0]
                item["extras"]["taxon:en"] = species.split(" (", 1)[1].removesuffix(")")
            else:
                item["extras"]["species"] = species
        if feature["Cultivar"] and feature["Cultivar"] != "Not Specified":
            if "taxon:en" in item["extras"].keys():
                item["extras"]["taxon:en"] = '{} "{}"'.format(item["extras"]["taxon:en"], feature["Cultivar"])
        # Ignore feature["Genus"] because it includes values such as
        # "Eucalyptus M to Z". feature["Species"] is used instead and is much
        # more useful and accurate.
        yield item
