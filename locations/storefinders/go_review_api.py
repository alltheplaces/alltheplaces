from typing import Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GoReviewApiSpider(JSONBlobSpider):
    """
    To use this spider, specify the 'domain' attribute as used in the request
    to https://admin.goreview.co.za/website/api/locations/search
    Alternatively, specify multiple 'domain' values in the 'domain_list'
    attribute.
    """

    start_urls: list[str] = ["https://admin.goreview.co.za/website/api/locations/search"]
    locations_key: str | list[str] = "stores"
    custom_settings: dict = {"ROBOTSTXT_OBEY": False}
    domain: str | None = None
    domain_list: list[str] | None = None

    async def start(self):
        if self.domain is not None:
            self.domain_list = [self.domain]
        if self.domain_list is not None:
            for domain in self.domain_list:
                data_raw = {
                    "domain": domain,
                    "latitude": "null",
                    "longitude": "null",
                    "attributes": "false",
                    "radius": "null",
                    "initialLoad": "true",
                }
                if len(self.start_urls) != 1:
                    raise ValueError("Specify one URL in the start_urls list attribute.")
                    return
                yield JsonRequest(url=self.start_urls[0], method="POST", data=data_raw)
        else:
            raise ValueError(
                "Either the GoReview 'domain' attribute must be set, or the 'domain_list' attribute must set to a list of 'domain' values."
            )

    def parse_feature_array(self, response: TextResponse, feature_array: list) -> Iterable[Feature]:
        for feature in feature_array:
            if feature.get("trading_status"):
                if feature.get("trading_status") != "Open":
                    continue
            self.pre_process_data(feature)
            item = DictParser.parse(feature)

            item["website"] = feature["local_page_url"]

            if feature.get("attributes") is not None:
                apply_yes_no(Extras.DELIVERY, item, "Delivery" in feature.get("attributes"))
                apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-through" in feature.get("attributes"))
                apply_yes_no(Extras.TAKEAWAY, item, "Takeaway" in feature.get("attributes"))

            yield from self.post_process_item(item, response, feature)
