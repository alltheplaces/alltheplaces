from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DedemanROSpider(JSONBlobSpider):
    name = "dedeman_ro"
    item_attributes = {"brand": "Dedeman", "brand_wikidata": "Q5249762"}
    start_urls = ["https://www.dedeman.ro/ro/suport-clienti/magazine-dedeman"]

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(
            response.xpath('//*[@class="dedeman-network"]/@data-mage-init').re_first(r'{\s*"stores":\s*(\[.+?]),')
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        yield item
