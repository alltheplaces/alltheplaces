from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class BoboliESPTSpider(JSONBlobSpider):
    name = "boboli_es_pt"
    item_attributes = {"brand": "Boboli", "brand_wikidata": "Q39073733"}
    allowed_domains = ["www.boboli.es"]
    start_urls = [
        "https://www.boboli.es/es/tiendas?all=1&id_country=6", # ES
        "https://www.boboli.es/es/tiendas?all=1&id_country=15", # PT
    ]
    needs_json_request = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["active"] != 1:
            return

        item["ref"] = str(feature["id_store"])
        match feature["id_country"]:
            case 6:
                item["country"] = "ES"
            case 15:
                item["country"] = "PT"
        item["branch"] = feature["storeName"].removeprefix("El Corte Inglés ")
        item.pop("name", None)
        item["street_address"] = merge_address_lines([feature.get("address1"), feature.get("address2")])

        apply_category(Categories.SHOP_CLOTHES, item)
        item["extras"]["alt_ref"] = str(feature["store_identifier"])
        yield item
