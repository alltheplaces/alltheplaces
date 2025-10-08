from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CasaDoPaoDeQueijoBRSpider(JSONBlobSpider):
    name = "casa_do_pao_de_queijo_br"
    item_attributes = {"brand": "Casa do Pão de Queijo", "brand_wikidata": "Q9698946"}
    start_urls = ["http://www.casadopaodequeijo.com.br/service/lojascpq"]
    locations_key = "res"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = feature["endereco"]
        item["state"] = feature["uf"]
        item["postcode"] = feature["cep"]
        apply_category(Categories.COFFEE_SHOP, item)
        yield item
