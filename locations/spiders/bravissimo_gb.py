from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class BravissimoGBSpider(JSONBlobSpider):
    name = "bravissimo_gb"
    item_attributes = {"name": "Bravissimo", "brand": "Bravissimo", "brand_wikidata": "Q4958430"}
    start_urls = ["https://www.bravissimo.com/shops/all/"]

    def extract_json(self, response):
        searchstr = '"all":'
        script = response.xpath(f"//script[contains(text(), '{searchstr}')]/text()").get()
        start = script.find(searchstr) + len(searchstr)
        locations = chompjs.parse_js_object(script[start:])
        return locations

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        if feature.get("address3"):
            item["street_address"] = merge_address_lines(
                [feature["address"]["address2"], feature["address"]["address3"]]
            )
        else:
            item["street_address"] = feature["address"]["address2"]
        item["website"] = "https://www.bravissimo.com/shops/" + feature["slug"] + "/"
        apply_category(Categories.SHOP_CLOTHES, item)
        apply_clothes([Clothes.UNDERWEAR], item)
        yield item
