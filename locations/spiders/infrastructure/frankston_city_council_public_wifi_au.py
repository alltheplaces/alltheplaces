from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.flatgeobuf_spider import FlatGeobufSpider
from locations.items import Feature


class FrankstonCityCouncilPublicWifiAUSpider(FlatGeobufSpider):
    name = "frankston_city_council_public_wifi_au"
    item_attributes = {
        "operator": "Frankston City Council",
        "operator_wikidata": "Q132472668",
        "state": "VIC",
        "nsi_id": "N/A",
    }
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/frankston-publisher/Community/Public_WiFi.fgb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.ANTENNA, item)
        apply_category({"internet_access": "wlan"}, item)
        apply_category({"internet_access:fee": "customers"}, item)
        apply_cateogry({"internet_access:operator": self.item_attributes["operator"]}, item)
        apply_category({"internet_access:operator:wikidata": self.item_attributes["operator_wikidata"]}, item)
        yield item
