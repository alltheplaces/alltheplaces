from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CityOfMelbourneBarbecuesAUSpider(JSONBlobSpider):
    name = "city_of_melbourne_barbecues_au"
    item_attributes = {"operator": "City of Melbourne", "operator_wikidata": "Q1919098"}
    allowed_domains = ["maps.melbourne.vic.gov.au"]
    start_urls = ["https://maps.melbourne.vic.gov.au/weave/services/v1/feature/getFeatures?shape=POLYGON((278984.5214999998%205773194.2749,278984.5214999998%205853194.1042,361023.5938999998%205853194.1042,361023.5938999998%205773194.2749,278984.5214999998%205773194.2749))&entityId=lyr_barbeque&datadefinition=__dd__ar_barbeque&outCrs=EPSG:4326&inCrs=EPSG:7855&operation=intersects&returnCentroid=true&returnFirst=false"]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["properties"]["__dd__ar_barbeque"][0])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["np_assetid"])
        item["addr_full"] = feature["st_location_desc"]
        apply_category(Categories.BARBECUE, item)
        yield item

