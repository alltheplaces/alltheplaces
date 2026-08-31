import json
from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import Request, Response, TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class OrEnCashFRSpider(JSONBlobSpider):
    name = "or_en_cash_fr"
    item_attributes = {"brand": "Or en Cash", "brand_wikidata": "Q115088395"}
    allowed_domains = ["www.orencash.fr"]
    start_urls = ["https://www.orencash.fr/boutiques-achat-or/"]

    def extract_json(self, response: Response) -> Iterable[Request]:
        raw_data = json.loads(response.xpath('//*[@class="office-index__map"]//@data-offices').get())
        return raw_data

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["website"] = urljoin("https://www.orencash.fr/", item["website"])
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name").replace("Or En Cash ", "")
        yield item
