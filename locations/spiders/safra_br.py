from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SafraBRSpider(JSONBlobSpider):
    name = "safra_br"
    item_attributes = {"brand": "Banco Safra", "brand_wikidata": "Q4116096"}
    start_urls = ["https://www.safra.com.br/lumis/api/rest/agencies/lumgetdata/listAgencies"]
    locations_key = "rows"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = feature["adress"]
        item["postcode"] = feature["cep"]
        apply_category(Categories.BANK, item)
        yield item
