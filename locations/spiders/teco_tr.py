import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TecoTRSpider(JSONBlobSpider):
    name = "teco_tr"
    item_attributes = {"brand": "Teco", "brand_wikidata": "Q126904377"}
    start_urls = ["https://www.teco.com.tr/bayiler.php"]

    def extract_json(self, response: Response) -> list[dict]:
        match = re.search(
            r"const dealers = (\[.*?\]);\s*dealers\.forEach",
            response.text,
            re.S,
        )
        return json.loads(match.group(1))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.FUEL_STATION, item)
        yield item
