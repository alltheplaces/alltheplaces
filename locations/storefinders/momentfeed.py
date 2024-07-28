import urllib.parse

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class MomentFeedSpider(Spider):
    dataset_attributes = {"source": "api", "api": "momentfeed.com"}

    id = ""

    page_size = 100

    def start_requests(self):
        yield JsonRequest(
            url=f"https://api.momentfeed.com/v1/analytics/api/llp.json?auth_token={self.id}&pageSize={self.page_size}&page=1"
        )

    def parse(self, response, **kwargs):
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
            page = int(urllib.parse.parse_qs(urllib.parse.urlparse(response.url).query)["page"][0])
            yield JsonRequest(
                url=f"https://api.momentfeed.com/v1/analytics/api/llp.json?auth_token={self.id}&pageSize={self.page_size}&page={page + 1}"
            )

    def parse_item(self, item, feature, store_info, **kwargs):
        yield item
