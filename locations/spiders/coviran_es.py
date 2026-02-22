from typing import Iterable
from urllib.parse import urljoin

from chompjs import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CoviranESSpider(JSONBlobSpider):
    name = "coviran_es"
    item_attributes = {"brand": "Covirán", "brand_wikidata": "Q61070539"}
    start_urls = ["https://www.coviran.es/localizador"]

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(response.xpath('//script[contains(text(), "var tiendasData")]/text()').get())[
            "data"
        ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "Coviran" not in item["name"].title():
            return
        item["branch"] = (
            item.pop("name").replace("SUPERMERCADOS", "").replace("SUPERMERCADO", "").strip().removeprefix("COVIRAN ")
        )
        item["street_address"] = item.pop("addr_full", None)
        if isinstance(feature.get("phone"), list):
            item["phone"] = "; ".join(filter(None, [phone.get("phone") for phone in feature["phone"]]))
        item["website"] = urljoin("https://tienda.coviran.es/", feature.get("slug"))

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
