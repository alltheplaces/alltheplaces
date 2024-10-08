from json import loads
from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.meny_no import MenyNOSpider


class MenyDKSpider(JSONBlobSpider):
    name = "meny_dk"
    item_attributes = MenyNOSpider.item_attributes
    allowed_domains = ["meny.dk"]
    start_urls = ["https://meny.dk/search"]
    locations_key = ["response", "docs"]

    def start_requests(self) -> Iterable[JsonRequest]:
        data = {
            "params": {"wt": "json"},
            "filter": [],
            "query": 'ss_search_api_datasource:"entity:node" AND bs_status:true AND ss_type:"store"',
            "limit": 1000,
        }
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature["ss_field_store_viking_id"]
        feature["name"] = feature["tm_X3b_en_title"]
        feature["lat"], feature["lon"] = feature["locs_latlon"].split(",", 1)
        feature["street_address"] = feature["tm_X3b_en_address_line1"][0]
        feature["city"] = feature["tm_X3b_en_locality"][0]
        feature["postcode"] = feature["tm_X3b_en_postal_code"][0]
        feature["phone"] = feature["ss_field_store_phone"]
        feature["website"] = feature.get("ss_field_custom_pane_link")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        for day_hours in loads(feature["sm_solr_opening_hours"][0]):
            item["opening_hours"].add_range(
                DAYS_3_LETTERS_FROM_SUNDAY[day_hours["day"]],
                str(day_hours["starthours"]).zfill(4),
                str(day_hours["endhours"]).zfill(4),
                "%H%M",
            )
        yield item
