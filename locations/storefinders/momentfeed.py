import urllib.parse

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

class MomentFeedSpider(Spider):
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

    def start_requests(self):
        yield JsonRequest(
            url=f"https://uberall.com/api/mf-lp-adapter/llp.json?center=0,0&coordinates=-90,180,90,-180&pageSize={self.page_size}&page=1",
            headers={"Authorization": self.api_key},
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
            item["street_address"] = merge_address_lines([store_info["address_extended"], store_info["address"]])
            item.pop("addr_full", None)

            item["opening_hours"] = OpeningHours()
            open_days = []
            for day in store_info["store_hours"].split(";"):
                rule = day.split(",")
                if len(rule) == 3:
                    open_days.append(DAYS[int(rule[0]) - 1])
                    item["opening_hours"].add_range(DAYS[int(rule[0]) - 1], rule[1], rule[2].replace("2400", "2359"), "%H%M")
            closed_days = list(set(DAYS) - set(open_days))
            for closed_day in closed_days:
                item["opening_hours"].set_closed(closed_day)

            for provider in store_info["providers"]:
                if provider["_type"] == "Facebook":
                    item["facebook"] = provider["url"]
                elif provider["_type"] == "Google" and provider.get("place_id"):
                    item["extras"]["ref:google:place_id"] = provider["place_id"]

            yield from self.parse_item(item, feature, store_info)

        if len(response.json()) == self.page_size:
            next_page = int(urllib.parse.parse_qs(urllib.parse.urlparse(response.url).query)["page"][0]) + 1
            yield JsonRequest(
                url=f"https://uberall.com/api/mf-lp-adapter/llp.json?center=0,0&coordinates=-90,180,90,-180&pageSize={self.page_size}&page={next_page}",
                headers={"Authorization": self.api_key},
            )

    def parse_item(self, item: Feature, feature: dict, store_info: dict):
        yield item
