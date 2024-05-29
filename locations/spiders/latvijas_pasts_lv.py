import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class LatvijasPastsLVSpider(Spider):
    name = "latvijas_pasts_lv"
    item_attributes = {"brand": "Latvijas Pasts", "brand_wikidata": "Q1807088"}
    start_urls = ["https://pasts.lv/ajax/module:post_office/"]
    no_refs = True
    custom_settings = {"DOWNLOADER_CLIENT_TLS_CIPHERS": "DEFAULT:!DH"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.json()["all"]):
            item = Feature()
            item["lat"] = location["tmpLat"]
            item["lon"] = location["tmpLong"]
            item["addr_full"] = location["tmpAddress"]

            if location["tmpCategory"] == 1:
                item["name"] = location["tmpName"]
                apply_category(Categories.POST_OFFICE, item)
            elif location["tmpCategory"] == 4:
                apply_category(Categories.POST_BOX, item)
            elif location["tmpCategory"] == 5:
                apply_category(Categories.PARCEL_LOCKER, item)
            else:
                continue

            yield item
