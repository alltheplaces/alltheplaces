from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class BancoDesioITSpider(JSONBlobSpider):
    name = "banco_desio_it"
    item_attributes = {"brand": "Banco Desio", "brand_wikidata": "Q3633825"}
    start_urls = ["https://www.bancodesio.it/it/filiali-json/all"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["field_cab"]
        item["email"] = feature["field_email"]
        item["phone"] = feature["field_telefono"]
        item["addr_full"] = clean_address(feature["searchtext"])
        item["website"] = "https://www.bancodesio.it" + feature["path"]
        apply_category(Categories.BANK, item)
        yield item
