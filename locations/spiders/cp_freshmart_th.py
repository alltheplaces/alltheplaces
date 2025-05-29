from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CPFreshmartTHSpider(JSONBlobSpider):
    name = "cp_freshmart_th"
    item_attributes = {"brand": "CP Freshmart", "brand_wikidata": "Q125917787", "country": "TH"}

    def start_requests(self):
        yield JsonRequest(
            url="https://cpfmapi.addressasia.com/wp-json/store/v2/collect?lang=th",
            method="POST",
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
