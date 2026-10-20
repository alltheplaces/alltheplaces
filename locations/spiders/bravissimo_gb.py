import json
import chompjs
from scrapy.spiders import SitemapSpider

from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Request, TextResponse

from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.categories import Categories, apply_category, Clothes, apply_clothes

class BravissimoGBSpider(JSONBlobSpider):
    name = "bravissimo_gb"
    item_attributes = {"brand": "Bravissimo", "brand_wikidata": "Q4958430"}
    start_urls = ["https://www.bravissimo.com/shops/all/"]

    def extract_json(self, response):
        searchstr = '"all":'
        script = response.xpath(f"//script[contains(text(), '{searchstr}')]/text()").get()
        start = script.find(searchstr) + len(searchstr)
        locations = chompjs.parse_js_object(script[start:])
        return locations

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        print(feature)
        item["branch"] = item.pop("name")
        if item.get("address3"):
            item["street_address"] = merge_address_lines([feature["address"]["address2"],feature["address"]["address3"]])
        else:
            item["street_address"] = feature["address"]["address2"]
        item["website"] = "https://www.bravissimo.com/shops/" + feature["slug"] + "/"
        apply_category(Categories.SHOP_CLOTHES, item)
        apply_clothes([Clothes.UNDERWEAR], item)
        yield item
