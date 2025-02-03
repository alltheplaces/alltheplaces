from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MelbourneCityCouncilDogParksAUSpider(JSONBlobSpider):
    name = "melbourne_city_council_dog_parks_au"
    item_attributes = {"operator": "Melbourne City Council", "operator_wikidata": "Q56477763", "nsi_id": "N/A"}
    allowed_domains = ["maps.melbourne.vic.gov.au"]
    start_urls = [
        "https://maps.melbourne.vic.gov.au/weave/services/v1/feature/getFeatures?shape=POLYGON((278984.5214999998%205773194.2749,278984.5214999998%205853194.1042,361023.5938999998%205853194.1042,361023.5938999998%205773194.2749,278984.5214999998%205773194.2749))&entityId=lyr_dogoffleash&datadefinition=__dd__ar_dogoffleash&outCrs=EPSG:4326&inCrs=EPSG:7855&operation=intersects&returnCentroid=true&returnFirst=false"
    ]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["properties"]["__dd__ar_dogoffleash"][0])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["st_management"] and feature["st_management"] != "Managed by City of Melbourne":
            # Dog off-leash area on private/other land not operated by the
            # City of Melbourne. Ignore as operator not specified.
            return
        item["ref"] = str(feature["_id"])
        item["name"] = feature["st_description"]
        apply_category(Categories.LEISURE_DOG_PARK, item)
        yield item
