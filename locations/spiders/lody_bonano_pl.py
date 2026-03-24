from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LodyBonanoPLSpider(JSONBlobSpider):
    name = "lody_bonano_pl"
    item_attributes = {"brand": "Lody Bonano", "brand_wikidata": "Q126195991"}
    start_urls = ["https://www.lodybonano.pl/nasze-lodziarnie"]
    no_refs = True

    def extract_json(self, response: Response) -> dict | list[dict]:
        locations = chompjs.parse_js_object(response.xpath('//script[contains(text(), "var placesList")]/text()').get())
        return locations

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = feature.get("description")
        item["name"] = None
        item["website"] = response.url
        apply_category(Categories.ICE_CREAM, item)
        yield item
