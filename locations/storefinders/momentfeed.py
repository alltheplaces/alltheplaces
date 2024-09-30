import urllib.parse

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class MomentFeedSpider(Spider, AutomaticSpiderGenerator):
    """
    MomentFeed (owned by Uberall)
    https://momentfeed.com/

    To use, specify:
      - `api_key`: mandatory parameter
      - `page_size`: optional parameter, default value is 100
    """

    dataset_attributes = {"source": "api", "api": "momentfeed.com"}
    api_key: str = ""
    page_size: int = 100
    detection_rules = [
        DetectionRequestRule(
            url=r"^https?:\/\/api\.momentfeed\.com\/v1\/analytics\/api\/llp\/meta\.json\?.*?(?<=[?&])auth_token=(?P<api_key>[A-Z]+)(?:&|$)"
        ),
        DetectionRequestRule(
            url=r"^https?:\/\/uberall\.com\/api\/mf-lp-adapter\/llp\.json\?.*?(?<=[?&])auth_token=(?P<api_key>[A-Z]+)(?:&|$)"
        ),
    ]

    def start_requests(self):
        yield JsonRequest(
            url=f"https://api.momentfeed.com/v1/analytics/api/llp.json?auth_token={self.api_key}&pageSize={self.page_size}&page=1"
        )

    def parse(self, response: Response):
        if "message" in response.json():
            return

        for feature in response.json():
            if feature["status"] != "open":
                continue

            store_info = feature["store_info"]

            item = DictParser.parse(store_info)
            item["ref"] = store_info["corporate_id"]
            item["street_address"] = ", ".join(filter(None, [store_info["address"], store_info["address_extended"]]))
            item["addr_full"] = None

            oh = OpeningHours()
            for day in store_info["store_hours"].split(";"):
                rule = day.split(",")
                if len(rule) == 3:
                    oh.add_range(day=DAYS[int(rule[0]) - 1], open_time=rule[1], close_time=rule[2], time_format="%H%M")

            item["opening_hours"] = oh.as_opening_hours()

            for provider in store_info["providers"]:
                if provider["_type"] == "Facebook":
                    item["facebook"] = provider["url"]
                    break

            item["twitter"] = feature["twitter_handle"]

            yield from self.parse_item(item, feature, store_info)

        if len(response.json()) == self.page_size:
            next_page = int(urllib.parse.parse_qs(urllib.parse.urlparse(response.url).query)["page"][0]) + 1
            yield JsonRequest(
                url=f"https://api.momentfeed.com/v1/analytics/api/llp.json?auth_token={self.api_key}&pageSize={self.page_size}&page={next_page}"
            )

    def parse_item(self, item: Feature, feature: dict, store_info: dict):
        yield item
