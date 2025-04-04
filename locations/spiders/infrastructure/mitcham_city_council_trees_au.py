from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitchamCityCouncilTreesAUSpider(JSONBlobSpider):
    name = "mitcham_city_council_trees_au"
    item_attributes = {"operator": "Mitcham City Council", "operator_wikidata": "Q56477709", "state": "SA"}
    allowed_domains = ["dev.forestree.studio"]
    start_urls = ["https://dev.forestree.studio/storage/data/mitcham/mitcham_trees.geojson"]
    locations_key = "features"
    species = {}

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url="https://dev.forestree.studio/storage/data/mitcham/mitcham_all_species.geojson",
            callback=self.parse_species_list,
        )

    def parse_species_list(self, response: Response) -> Iterable[JsonRequest]:
        for species in response.json()["features"]:
            species_attribs = {
                "taxon_en": species["properties"].get("common_name"),
                "species": species["properties"].get("genus"),
            }
            species_id = str(species["id"])
            self.species[species_id] = species_attribs
        yield JsonRequest(url=self.start_urls[0])

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        apply_category(Categories.NATURAL_TREE, item)
        species_id = str(feature["sid"])
        if species_id in self.species.keys():
            item["extras"].update(self.species[species_id])
        elif species_id != "0":  # "0" is unknown species.
            raise ValueError("Invalid species identifier `{}`. Tree ignored.".format(species_id))
        if planted_year := feature.get("py"):
            item["extras"]["start_date"] = planted_year
        yield item
