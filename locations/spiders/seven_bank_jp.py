from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class SevenBankJPSpider(LocationCloudSpider):
    name = "seven_bank_jp"
    item_attributes = {"brand": "セブン銀行", "brand_wikidata": "Q7457182", "name": "セブン銀行"}
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    api_endpoint = "https://location.sevenbank.co.jp/sevenbank/api/proxy2/shop/list"
    website_formatter = "https://location.sevenbank.co.jp/sevenbank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = source_feature["name"].removesuffix("　共同出張所")
        item["extras"]["branch:ja-Hira"] = source_feature["ruby"]
        apply_category(Categories.ATM, item)
        yield item
