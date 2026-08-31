from typing import Iterable

import chompjs
from scrapy import FormRequest
from scrapy.http import Response, TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NaivasKESpider(JSONBlobSpider):
    name = "naivas_ke"
    item_attributes = {"brand": "Naivas", "brand_wikidata": "Q18379067"}
    start_urls = ["https://corporate.naivas.info/our-stores/"]
    locations_key = "data"

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        data_raw = response.xpath("//script[@id='naivas-map-js-js-extra']/text()").get()
        data_raw = data_raw.split("store_locator_ajax =", 1)[1]
        store_locator_ajax = chompjs.parse_js_object(data_raw)

        ajax_url = store_locator_ajax["ajax_url"]
        nonce = store_locator_ajax["nonce"]
        form_data = {"action": "get_stores", "nonce": nonce}

        yield FormRequest(url=ajax_url, formdata=form_data, callback=self.parse_stores)

    def parse_stores(self, response: TextResponse) -> Iterable[Feature]:
        features = self.extract_json(response)
        yield from self.parse_feature_array(response, features) or []

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        yield item
