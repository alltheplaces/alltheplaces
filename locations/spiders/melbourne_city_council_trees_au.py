from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MelbourneCityCouncilTreesAUSpider(JSONBlobSpider):
    name = "melbourne_city_council_trees_au"
    item_attributes = {"operator": "Melbourne City Council", "operator_wikidata": "Q56477763", "nsi_id": "N/A"}
    allowed_domains = ["data.melbourne.vic.gov.au"]
    start_urls = [
        "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/trees-with-species-and-dimensions-urban-forest/exports/json?lang=en&timezone=Australia%2FSydney"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_TIMEOUT": 60  # Large file to download
    }

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
            item["extras"]["start_time"] = date_planted
        elif year_planted := feature.get("year_planted"):
            item["extras"]["start_time"] = year_planted
        yield item
