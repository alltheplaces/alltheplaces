from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.flatgeobuf_spider import FlatGeobufSpider
from locations.items import Feature


class FrankstonCityCouncilDisabledParkingSpacesAUSpider(FlatGeobufSpider):
    name = "frankston_city_council_disabled_parking_spaces_au"
    item_attributes = {
        "operator": "Frankston City Council",
        "operator_wikidata": "Q132472668",
        "state": "VIC",
        "nsi_id": "N/A",
    }
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/frankston-publisher/Community/Accessible_Carpark.fgb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.PARKING_SPACE, item)
        item["extras"]["parking_space"] = "disabled"
        yield item
