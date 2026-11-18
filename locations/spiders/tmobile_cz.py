import json
import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TmobileCZSpider(JSONBlobSpider):
    name = "tmobile_cz"
    allowed_domains = ["coveragemap-tmcz.position.cz"]
    start_urls = ["https://coveragemap-tmcz.position.cz/map.php?M=ngMapWin1&W=1600&H=1200&EL=TMCZ:Store&lang=cz"]
    item_attributes = {"brand": "T-Mobile", "brand_wikidata": "Q327634"}

    def extract_json(self, response):
        p = re.compile(r"new AO\(([a-z0-9., ';-]+{[^}]+})\)")
        for m in p.finditer(response.text):
            item_str = (
                "["
                + m.group(1).replace("'", '"').replace('<BR><div class="siebui-emr-greeting">&nbsp;</div>', "")
                + "]"
            )
            item_json = json.loads(item_str)
            _shape, _coords, _x, _y, id, _descr, _pos, data = item_json
            data["id"] = id
            yield data

    def pre_process_data(self, feature: dict):
        feature["street_address"] = feature["address"]
        del feature["address"]
        feature["city"] = feature["a_city"]
        feature["postcode"] = feature["a_psc"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
