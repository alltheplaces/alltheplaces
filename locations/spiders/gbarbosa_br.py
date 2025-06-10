from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GbarbosaBRSpider(JSONBlobSpider):
    name = "gbarbosa_br"
    item_attributes = {"brand": "GBarbosa", "brand_wikidata": "Q10287817"}

    def start_requests(self):
        yield JsonRequest(
            url="https://www.gbarbosa.com.br/api/dataentities/LJ/search/?_fields=storeName,address,complement,city,state,businessHours,phone,storeType,storeLink,zipCode,city,state,id",
            headers={"REST-Range": "resources=0-500"},
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = (
            item.pop("name")
            .replace("Eletroshow", "")
            .replace("Farmácia", "")
            .replace("GBarbosa", "")
            .replace("Hiper", "")
            .lstrip()
        )
        if feature.get("storeLink"):
            item["lat"], item["lon"] = url_to_coords(feature["storeLink"])
        if feature["storeType"] == "Farmácia":
            apply_category(Categories.PHARMACY, item)
        elif feature["storeType"] in ["Eletro Show", "EletroShow"]:
            apply_category(Categories.SHOP_ELECTRONICS, item)
        elif feature["storeType"] in ["Hipermercado", "Supermercado"]:
            apply_category(Categories.SHOP_SUPERMARKET, item)
        else:
            self.crawler.stats.inc_value(f'atp/gbarbosa_br/unmapped_cat/{feature["storeType"]}')
        yield item
