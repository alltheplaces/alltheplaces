import json
from typing import Any

import chompjs
from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class AcquaSaponeITSpider(Spider):
    name = "acqua_sapone_it"
    item_attributes = {"brand": "Acqua & Sapone", "brand_wikidata": "Q51079044"}
    start_urls = ["https://www.acquaesapone.it/punti-vendita/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for region in json.loads(
            chompjs.parse_js_object(response.xpath('//script[@id="aespv/aesmapjs-js-extra"]/text()').get())[
                "aes_counter"
            ]
        ):
            yield FormRequest(
                "https://www.acquaesapone.it/wp-admin/admin-ajax.php",
                formdata={
                    "action": "aespv_filter_get_results",
                    "security": "4c7c902561",
                    "aespv_filter_regione": region["aes_regione"],
                },
                callback=self.parse_region,
            )

    def parse_region(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.json()["html"]):
            item = Feature()
            item["ref"] = location["uuid"] or location["permalink"]
            item["addr_full"] = location["indirizzo"]
            item["website"] = location["permalink"]
            item["phone"] = location["telefono"]

            apply_category(Categories.SHOP_CHEMIST, item)

            yield item
