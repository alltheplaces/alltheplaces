from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WhitehorseCityCouncilMchNurseClinicsAUSpider(JSONBlobSpider):
    name = "whitehorse_city_council_mch_nurse_clinics_au"
    item_attributes = {"operator": "Whitehorse City Council", "operator_wikidata": "Q56477787"}
    allowed_domains = ["map.whitehorse.vic.gov.au"]
    start_urls = [
        "https://map.whitehorse.vic.gov.au/weave/services/v1/feature/getFeatures?shape=POLYGON((16151350%20-4560956,16151350%20-4549585.473333315,16165750%20-4549585.473333315,16165750%20-4560956,16151350%20-4560956))&entityId=lyr_maternal_and_child_health_centres&datadefinition=dd_whm_maternal_and_child_health_centres&outCrs=EPSG:4326&inCrs=EPSG:3857&operation=intersects&returnCentroid=true"
    ]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["properties"]["dd_whm_maternal_and_child_health_centres"][0])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["_id"]
        apply_category(Categories.NURSE_CLINIC, item)
        yield item
