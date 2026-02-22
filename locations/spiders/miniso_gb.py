import chompjs
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.items import Feature


class MinisoGBSpider(JSONBlobSpider):
    name = "miniso_gb"
    item_attributes = {"brand": "Miniso", "brand_wikidata": "Q20732498"}
    start_urls = ["https://minisoshop.co.uk/store-locator"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        data_raw = response.xpath("//script[contains(text(), 'jsonLocations:')]/text()").get()
        data_raw = data_raw.replace("pageData.push({ stores: ", "").replace("});", "")
        data_raw = data_raw.split('jsonLocations: {"items":', 1)[1]
        features_dict = chompjs.parse_js_object(data_raw)
        return features_dict
