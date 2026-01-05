import string
from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AveveSpider(JSONBlobSpider):
    name = "aveve"
    item_attributes = {"brand": "Aveve", "brand_wikidata": "Q790683"}
    start_urls = ["https://www.aveve.be/nl/winkels/"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        json_data = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "stores:")]/text()').re_first(r"stores:\s?(\[\{.*?\}\])")
        )
        return json_data

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = string.capwords(item.pop("name").removeprefix("AVEVE "))
        item["website"] = item["extras"]["website:nl"] = feature["detailUrl"]
        item["extras"]["website:fr"] = "https://www.aveve.be/fr/magasins/{}/".format(feature["detailUrl"].split("/")[5])
        apply_category(Categories.SHOP_GARDEN_CENTRE, item)
        yield item
