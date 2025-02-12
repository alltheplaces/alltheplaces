import json
import re

from locations.categories import Categories
from locations.hours import DAYS_CZ, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class TmobileCZSpider(JSONBlobSpider):
    name = "tmobile_cz"
    allowed_domains = ["coveragemap-tmcz.position.cz"]
    start_urls = ["https://coveragemap-tmcz.position.cz/map.php?M=ngMapWin1&W=1600&H=1200&EL=TMCZ:Store&lang=cz"]
    item_attributes = {"brand": "T-Mobile", "brand_wikidata": "Q327634", "extras": Categories.SHOP_MOBILE_PHONE.value}

    def extract_json(self, response):
        p = re.compile(r"new AO\(([a-z0-9., ';-]+{[^}]+})\)")
        for m in p.finditer(response.text):
            item_str = "[" + m.group(1).replace("'", '"') + "]"
            item_json = json.loads(item_str)
            _shape, _coords, _x, _y, id, _descr, _pos, data = item_json
            data["id"] = id
            yield data

    def pre_process_data(self, feature: dict):
        feature["street_address"] = feature["address"]
        del feature["address"]
        feature["city"] = feature["a_city"]
        feature["postcode"] = feature["a_psc"]

    def post_process_item(self, item, response, feature: dict):
        oh = OpeningHours()
        for hrs in feature["openinghrs"]:
            oh.add_ranges_from_string(hrs, DAYS_CZ)
        item["opening_hours"] = oh
        yield item
