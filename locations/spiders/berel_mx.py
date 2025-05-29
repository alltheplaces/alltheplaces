from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.items import Feature


class BerelMXSpider(JSONBlobSpider):
    name = "berel_mx"
    item_attributes = {"brand": "Berel", "brand_wikidata": "Q108669250"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True
    locations_key = ["bloques", 0, "sucursales"]

    def start_requests(self):
        yield JsonRequest(
            url="https://berel-web-cms.playfuldemo.com/rest/basicpage",
            data={"id": "ubica-tienda"},
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = feature["direccion"]
        item["postcode"] = feature["cp"]
        item["state"] = feature["estado"]
        item["lat"] = feature["geo_latitud"]
        item["lon"] = feature["geo_longitud"]
        item["phone"] = feature["telefono"]
        apply_category(Categories.SHOP_PAINT, item)
        yield item
