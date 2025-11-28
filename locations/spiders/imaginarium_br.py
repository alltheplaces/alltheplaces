from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ImaginariumBRSpider(JSONBlobSpider):
    name = "imaginarium_br"
    item_attributes = {"brand": "imaginarium", "brand_wikidata": "Q115687683"}
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"rest-range": "resources=0-500"}}
    start_urls = [
        "https://loja.imaginarium.com.br/api/dataentities/NL/search?_fields=id,active,address,addressNumber,addressComplement,neighborhood,state,city,businessName,latitude,longitude,postalCode,primaryPhone,promocao"
    ]

    def pre_process_data(self, feature: dict) -> None:
        feature["address1"] = " ".join(filter(None, [feature.pop("address"), feature.pop("addressNumber")]))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_GIFT, item)
        yield item
