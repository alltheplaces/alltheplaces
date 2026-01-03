from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature


class ForestreeSpider(Spider):
    """
    Forestree is a hosted web application commonly used by municipal
    governments for managing street trees (as well as other types of trees
    such as those in parks and arboretums). The main website for Forestree is
    https://forestree.app/

    To use this spider, specify a `host` and `customer_id`.

    In the example URL of "https://trees.example.net/storage/data/ex/ex_trees.geojson":
      host = "trees.example.net"
      customer_id = "ex"

    If data cleanup is required, override the `post_process_item` method.
    """

    host: str
    customer_id: str

    _species: dict = {}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"https://{self.host}/storage/data/{self.customer_id}/{self.customer_id}_all_species.geojson",
            callback=self.parse_species_list,
        )

    def parse_species_list(self, response: TextResponse) -> Iterable[JsonRequest]:
        for species in response.json()["features"]:
            self._species[species["id"]] = {
                "protected": "yes",
                "genus": species["properties"]["genus"],
                "species": species["properties"]["species"],
                "taxon:en": species["properties"]["common_name"],
            }
        yield JsonRequest(
            url=f"https://{self.host}/storage/data/{self.customer_id}/{self.customer_id}_trees.geojson",
            callback=self.parse_trees_list,
        )

    def parse_trees_list(self, response: TextResponse) -> Iterable[Feature]:
        for tree in response.json()["features"]:
            item = Feature()
            item["ref"] = str(tree["id"])
            item["geometry"] = tree["geometry"]
            apply_category(Categories.NATURAL_TREE, item)
            if tree["properties"].get("sid") and tree["properties"]["sid"] in self._species.keys():
                for field_name, field_value in self._species[tree["properties"]["sid"]].items():
                    item["extras"][field_name] = field_value
            if dbh_cm := tree["properties"].get("dbh"):
                item["extras"]["diameter"] = f"{dbh_cm} cm"
            yield from self.post_process_item(item, response, tree)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
