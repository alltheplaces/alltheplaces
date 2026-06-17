from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WolseleyGBSpider(JSONBlobSpider):
    name = "wolseley_gb"
    item_attributes = {"brand": "Wolseley", "brand_wikidata": "Q8030423"}
    start_urls = ["https://www.wolseley.co.uk/all-branches/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"][
            "pageProps"
        ]["branches"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["identifier"]
        item["website"] = response.urljoin(f'https://www.wolseley.co.uk/branch/{feature["seoName"]}/')
        item["lat"], item["lon"] = feature["coordinates"]["latitude"], feature["coordinates"]["longitude"]
        item["branch"] = item.pop("name")
        if opening_hours := feature.get("openingBusinessHours")["hours"]:
            item["opening_hours"] = OpeningHours()
            for rule in opening_hours:
                if rule["closed"] == "true":
                    continue
                item["opening_hours"].add_range(rule["dayOfWeek"], rule["openingTime"], rule["closingTime"])

        apply_category(Categories.TRADE_PLUMBING, item)
        yield item
