from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class FrankstonCityCouncilBarbecuesAUSpider(OpendatasoftExploreSpider):
    name = "frankston_city_council_barbecues_au"
    item_attributes = {"operator": "Frankston City Council", "operator_wikidata": "Q132472668", "nsi_id": "N/A"}
    api_endpoint = "https://data.frankston.vic.gov.au/api/explore/v2.1/"
    dataset_id = "frankston-city-council-bbqs"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["asset_id"])
        item["state"] = "VIC"
        apply_category(Categories.BARBECUE, item)
        match feature["asset_subtype"]:
            case "Electric" | "Solar":
                item["extras"]["fuel"] = "electric"
            case "Gas":
                item["extras"]["fuel"] = "gas"
            case _:
                pass
        yield item
