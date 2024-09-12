from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GoReviewApiSpider(JSONBlobSpider):
    """
    To use this spider, specify the domain, used in the request
    to https://admin.goreview.co.za/website/api/locations/search
    """

    start_urls = ["https://admin.goreview.co.za/website/api/locations/search"]
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    domain = None

    def start_requests(self):
        data_raw = {
            "domain": self.domain,
            "latitude": "null",
            "longitude": "null",
            "attributes": "false",
            "radius": "null",
            "initialLoad": "true",
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", data=data_raw)

    def parse_feature_array(self, response: Response, feature_array: list) -> Iterable[Feature]:
        for feature in feature_array:
            if feature["trading_status"] != "Open":
                continue
            self.pre_process_data(feature)
            item = DictParser.parse(feature)

            item["website"] = feature["local_page_url"]

            if item.get("attributes") is not None:
                apply_yes_no(Extras.DELIVERY, item, "Delivery" in feature.get("attributes"))
                apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-through" in feature.get("attributes"))
                apply_yes_no(Extras.TAKEAWAY, item, "Takeaway" in feature.get("attributes"))

            yield from self.post_process_item(item, response, feature)
