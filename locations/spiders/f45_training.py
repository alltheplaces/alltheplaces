from typing import Iterable

from chompjs import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class F45TrainingSpider(JSONBlobSpider):
    name = "f45_training"
    item_attributes = {"brand": "F45 Training", "brand_wikidata": "Q64390973"}
    start_urls = ["https://f45training.com/find-a-studio/"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        json_data = chompjs.parse_js_object(
            response.xpath('//*[contains(text(),"G_STUDIOS")]').re_first(r"G_STUDIOS = (.*);")
        )
        return json_data

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("F45 ")
        if item.get("state") in ["Not Applicable(N/A)", "N/A"]:
            item["state"] = None
        item["website"] = (
            f'https://f45training.com/{feature["country_code"].lower()}/studio/{feature["slug"]}/'.replace(
                "com/us/", "com/"
            )
            .replace("/gb/", "/uk/")
            .replace("com/kr/", "kr/")
        )
        apply_category(Categories.GYM, item)
        yield item
