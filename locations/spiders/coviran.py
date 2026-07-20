from typing import Any, Iterable

from chompjs import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.react_server_components import parse_rsc


class CoviranSpider(JSONBlobSpider):
    name = "coviran"
    item_attributes = {"brand": "Covirán", "brand_wikidata": "Q61070539"}
    start_urls = [
        "https://www.coviran.es/shops",
        "https://www.coviran.pt/shops",
    ]

    def extract_json(self, response: Response) -> list[dict]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for n, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        return self.find_shops(dict(parse_rsc(rsc.encode())))

    def find_shops(self, node: Any) -> list[dict]:
        if isinstance(node, dict):
            shops = node.get("shops")
            if isinstance(shops, list) and shops and isinstance(shops[0], dict) and "location" in shops[0]:
                return shops
            for value in node.values():
                if found := self.find_shops(value):
                    return found
        elif isinstance(node, list):
            for value in node:
                if found := self.find_shops(value):
                    return found
        return []

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["operator"] = item.pop("name")
        item["country"] = "PT" if ".coviran.pt" in response.url else "ES"
        item["street_address"] = item.pop("addr_full", None)
        item["phone"] = "; ".join(entry["phone"] for entry in feature.get("phone") or [] if entry.get("phone"))

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
