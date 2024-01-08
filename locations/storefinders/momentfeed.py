import re
import urllib.parse

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class MomentFeedSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "momentfeed.com"}
    api_key = ""
    page_size = 100

    def start_requests(self):
        yield JsonRequest(
            url=f"https://api.momentfeed.com/v1/analytics/api/llp.json?auth_token={self.api_key}&pageSize={self.page_size}&page=1"
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
                url=f"https://api.momentfeed.com/v1/analytics/api/llp.json?auth_token={self.api_key}&pageSize={self.page_size}&page={page+1}"
            )

    def parse_item(self, item, feature, store_info, **kwargs):
        yield item

    @staticmethod
    def storefinder_exists(response: Response) -> bool | Request:
        if response.xpath('//script[contains(@src, "web-assets-cdn.momentfeed.com/llp/")]'):
            return True
        return False

    @staticmethod
    def extract_spider_attributes(response: Response) -> dict | Request:
        if response.xpath('//script[contains(@src, "/scripts/app-")]'):
            appjs_uris = response.xpath('//script[contains(@src, "/scripts/app-")]/@src')
            if len(appjs_uris) == 1:
                return response.follow(
                    url=appjs_uris[0],
                    meta={
                        "next_extraction_method": MomentFeedSpider.extract_spider_attributes_appjs,
                    },
                    dont_filter=True,
                )
            elif len(appjs_uris) > 1:
                first_appjs_uri = appjs_uris.pop()
                return response.follow(
                    url=first_appjs_uri,
                    meta={
                        "next_extraction_method": MomentFeedSpider.extract_spider_attributes_appjs,
                        "extra_appjs_uris": appjs_uris,
                    },
                    dont_filter=True,
                )
        return {}

    @staticmethod
    def extract_spider_attributes_appjs(response: Response) -> dict | Request:
        if m := re.search(r".constant\s*\(\s*['\"]API_TOKEN['\"],\s*['\"]([A-Z]{16})['\"]\s*\)", response.text):
            return {
                "api_key": m.group(1),
            }
        elif response.meta.get("extra_appjs_uris"):
            appjs_uris = response.meta["extra_appjs_uris"]
            next_appjs_uri = appjs_uris.pop()
            if len(appjs_uris) == 0:
                return response.follow(
                    url=next_appjs_uri,
                    meta={
                        "next_extraction_method": MomentFeedSpider.extract_spider_attributes_appjs,
                    },
                    dont_filter=True,
                )
            elif len(appjs_uris) > 0:
                return response.follow(
                    url=next_appjs_uri,
                    meta={
                        "next_extraction_method": MomentFeedSpider.extract_spider_attributes_appjs,
                        "extra_appjs_uris": appjs_uris,
                    },
                    dont_filter=True,
                )
        return {}
