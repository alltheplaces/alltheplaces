import json
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class PaperSourceUSSpider(JSONBlobSpider):
    name = "paper_source_us"
    item_attributes = {"brand": "Paper Source", "brand_wikidata": "Q25000269"}
    start_urls = ["https://www.papersource.com/a/stores"]

    def extract_json(self, response: Response) -> list[dict]:
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        return data["props"]["pageProps"]["stores"]["content"]

    def pre_process_data(self, feature: dict) -> None:
        for key in ["description", "facebookLink", "instagramLink", "twitterLink"]:
            feature.pop(key, None)
        feature["lon"], feature["lat"] = feature.pop("location")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["opening_hours"] = OpeningHours()
        for rule in feature.get("hoursList") or []:
            if not (day := sanitise_day(rule["dayName"])):
                continue
            close_hour, _, close_minute = rule["closeTime"].partition(":")
            if int(close_hour) < 12:  # Source times are 12-hour without meridiem; closing times are PM
                close_hour = str(int(close_hour) + 12)
            item["opening_hours"].add_range(day, rule["openTime"], f"{close_hour}:{close_minute}")
        apply_category(Categories.SHOP_STATIONERY, item)
        yield item
