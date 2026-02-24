from typing import Iterable

import chompjs
from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.react_server_components import parse_rsc


class BerelMXSpider(JSONBlobSpider):
    name = "berel_mx"
    item_attributes = {"brand": "Berel", "brand_wikidata": "Q108669250"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True
    locations_key = ["bloques", 0, "sucursales"]
    start_urls = ["https://berel.com/ubica-tienda"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        scripts = response.xpath('//script[contains(text(), "sucursales")]/text()').getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        return DictParser.get_nested_key(dict(parse_rsc(rsc)), "sucursales")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = feature["direccion"]
        item["postcode"] = feature["cp"]
        item["state"] = feature["estado"]
        item["lat"] = feature["geo_latitud"]
        item["lon"] = feature["geo_longitud"]
        item["phone"] = feature["telefono"]
        apply_category(Categories.SHOP_PAINT, item)
        yield item
