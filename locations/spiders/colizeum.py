import json
import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ColizeumSpider(JSONBlobSpider):
    name = "colizeum"
    item_attributes = {
        "brand": "Colizeum",
        "brand_wikidata": "Q139567421",
    }
    start_urls = ["https://colizeumarena.com/arenas/"]

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        script = response.xpath("//script[@id='colizeum-arena-js-before']/text()").get("")
        match = re.search(r"var clzmClubMapData = (\[.*?\]);", script, re.DOTALL)
        return json.loads(match.group(1))

    def pre_process_data(self, feature: dict) -> None:
        if coords := feature.get("coordinates"):
            feature["lat"] = coords[0]
            feature["lon"] = coords[1]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        branch = feature.get("name", "").removeprefix("COLIZEUM ").strip()
        if branch:
            item["branch"] = branch
        item.pop("name", None)

        if site := feature.get("site"):
            item["website"] = site if site.startswith("http") else f"https://{site}"

        apply_category(Categories.INTERNET_CAFE, item)
        apply_yes_no("service:gaming", item, True)

        yield item
