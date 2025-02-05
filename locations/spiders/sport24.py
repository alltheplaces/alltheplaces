from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class Sport24Spider(JSONBlobSpider):
    name = "sport24"
    item_attributes = {"brand": "Sport 24", "brand_wikidata": "Q121503172"}
    start_urls = ["https://www.sport24.dk/stores/"]
    skip_auto_cc_domain = True

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"][
            "pageProps"
        ]["stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["navLocationCode"]
        item["website"] = response.urljoin(f'{feature["link"].strip()}/')
        item["lat"], item["lon"] = feature["locationCoordinates"].split(",")
        item["branch"] = item.pop("name")
        item["name"] = feature.get("type")
        item["street_address"] = item.pop("street")
        apply_category(Categories.SHOP_SPORTS, item)
        yield item
