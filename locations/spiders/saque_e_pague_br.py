from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SaqueEPagueBRSpider(JSONBlobSpider):
    name = "saque_e_pague_br"
    item_attributes = {"brand": "Saque e Pague"}
    # The store locator at https://www.saqueepague.com.br/encontre-um-ponto fetches its ATM list from this gist.
    start_urls = [
        "https://gist.githack.com/mktsep/1d73f0c30b1786b046e7d818a8b49e70/raw/3880eddec0db71b5f65d59e43246e449a15cd083/atms.json"
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["numero_logico"]
        item["located_in"] = item.pop("name").removesuffix(" - " + item["ref"]).strip()
        item["name"] = self.item_attributes["brand"]
        item["addr_full"] = feature["endereco"]
        item["city"] = feature["cidade"]
        item["state"] = feature["estado"]
        apply_category(Categories.ATM, item)
        yield item
