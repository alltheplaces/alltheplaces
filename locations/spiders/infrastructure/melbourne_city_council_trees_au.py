from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class MelbourneCityCouncilTreesAUSpider(OpendatasoftExploreSpider):
    name = "melbourne_city_council_trees_au"
    item_attributes = {"operator": "Melbourne City Council", "operator_wikidata": "Q56477763", "state": "VIC", "nsi_id": "N/A"}
    api_endpoint = "https://data.melbourne.vic.gov.au/api/explore/v2.1/"
    dataset_id = "trees-with-species-and-dimensions-urban-forest"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["com_id"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["species"] = feature["scientific_name"]
        item["extras"]["genus"] = feature["genus"]
        item["extras"]["taxon:en"] = feature["common_name"]
        item["extras"]["protected"] = "yes"
        if dbh := feature.get("diameter_breast_height"):
            item["extras"]["diameter"] = f"{dbh} cm"
        if date_planted := feature.get("date_planted"):
            item["extras"]["start_date"] = date_planted
        elif year_planted := feature.get("year_planted"):
            item["extras"]["start_date"] = year_planted
        yield item
