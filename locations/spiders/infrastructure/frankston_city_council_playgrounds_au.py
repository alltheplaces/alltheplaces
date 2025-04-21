from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class FrankstonCityCouncilPlaygroundsAUSpider(OpendatasoftExploreSpider):
    name = "frankston_city_council_playgrounds_au"
    item_attributes = {"operator": "Frankston City Council", "operator_wikidata": "Q132472668", "nsi_id": "N/A"}
    api_endpoint = "https://data.frankston.vic.gov.au/api/explore/v2.1/"
    dataset_id = "frankston-city-council-playgrounds"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["asset_id"])
        item["state"] = "VIC"
        apply_category(Categories.LEISURE_PLAYGROUND, item)
        yield item
