import json
from typing import Iterable

from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EverlastGymsSpider(JSONBlobSpider):
    name = "everlast_gyms"
    item_attributes = {
        "brand_wikidata": "Q112947134",
        "brand": "Everlast Gyms",
    }
    start_urls = ["https://www.everlastgyms.com/page-data/join/page-data.json"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "www.everlastgyms.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:158.0) Gecko/20100101 Firefox/158.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "same-origin",
            "Sec-Fetch-Site": "same-origin",
        },
    }

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        json_data = response.json()["result"]["data"]["storyblokEntry"]["content"]
        json_data = json.loads(json_data)["body"][0]["gyms"]
        return json_data

    def pre_process_data(self, feature: dict) -> None:
        feature["address"] = feature["content"]["address"]
        feature["email"] = feature["content"]["email"]["url"]
        feature["phone"] = feature["content"]["contact_number"]
        feature["url"] = feature["content"]["page_url"]["url"]
        feature["lat"], feature["lon"] = feature["content"]["coordinates"].split(",")
        feature["opening_hours"] = feature["content"]["opening_times"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item.pop("facebook", None)
        item.pop("twitter", None)
        if feature["opening_hours"]:
            item["opening_hours"] = OpeningHours()
            for day in feature["opening_hours"]:
                range = day["entries"][0]["days"] + " : " + day["entries"][0]["hours"]
                item["opening_hours"].add_ranges_from_string(ranges_string=range)
        apply_category(Categories.GYM, item)
        yield item
