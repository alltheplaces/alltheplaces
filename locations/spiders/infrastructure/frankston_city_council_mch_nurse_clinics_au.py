from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.flatgeobuf_spider import FlatGeobufSpider
from locations.hours import OpeningHours
from locations.items import Feature


class FrankstonCityCouncilMchNurseClinicsAUSpider(FlatGeobufSpider):
    name = "frankston_city_council_mch_nurse_clinics_au"
    item_attributes = {
        "operator": "Frankston City Council",
        "operator_wikidata": "Q132472668",
        "state": "VIC",
        "nsi_id": "N/A",
    }
    allowed_domains = ["connect.pozi.com"]
    start_urls = [
        "https://connect.pozi.com/userdata/frankston-publisher/Family-Services/Maternal_and_Child_Health_Centres.fgb"
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("phone", None)
        if hours_string := feature.get("Opening Hours"):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
        apply_category(Categories.NURSE_CLINIC, item)
        yield item
