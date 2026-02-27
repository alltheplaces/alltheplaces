import json
from typing import Iterable

from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FoodstuffsNZSpider(JSONBlobSpider):
    name = "foodstuffs_nz"
    requires_proxy = True
    start_urls = ["https://www.newworld.co.nz/", "https://www.paknsave.co.nz/"]
    BRANDS = {"newworld": ("New World", "Q7012488"), "paknsave": ("PAK'nSAVE", "Q7125339")}

    def extract_json(self, response: Response) -> dict | list[dict]:
        return json.loads(response.xpath('//script[@id="__NEXT_DATA__" and @type="application/json"]/text()').get())[
            "props"
        ]["pageProps"]["fallback"]["stores-physical"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item["name"]:
            item["branch"] = item.pop("name").removeprefix("PAK'nSAVE ").removeprefix("New World ")
        brand = response.url.split(".")[1]
        if brand_details := self.BRANDS.get(brand):
            item["brand"], item["brand_wikidata"] = brand_details
        item["opening_hours"] = OpeningHours()
        for rules in feature["openingHours"]:
            item["opening_hours"].add_range(rules["day"], rules["open"], rules["close"], "%I:%M %p")
        yield item
