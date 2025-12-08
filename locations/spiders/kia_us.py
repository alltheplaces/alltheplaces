from typing import AsyncIterator

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import postal_regions


class KiaUSSpider(scrapy.Spider):
    name = "kia_us"
    item_attributes = {"brand": "Kia", "brand_wikidata": "Q35349"}

    # https://www.kia.com/us/services/en/dealers/features
    SERVICE_FEATURE_IDS = [7, 14]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for index, record in enumerate(postal_regions("US")):
            if index % 140 == 0:
                yield JsonRequest(
                    url="https://www.kia.com/us/services/en/dealers/search",
                    data={"type": "zip", "zipCode": record["postal_region"]},
                    headers={"Referer": "https://www.kia.com/us/en/find-a-dealer/"},
                )

    def parse(self, response, **kwargs):
        for dealer in response.json():
            dealer.update(dealer.pop("location"))
            item = DictParser.parse(dealer)
            item["ref"] = dealer.get("code")
            item["street_address"] = dealer.get("street1")
            if phones := dealer.get("phones"):
                item["phone"] = phones[0].get("number")

            sales_item = item.deepcopy()
            apply_category(Categories.SHOP_CAR, sales_item)
            yield sales_item

            if any(x in dealer.get("featureIds", []) for x in self.SERVICE_FEATURE_IDS):
                service_item = item.deepcopy()
                service_item["ref"] = item["ref"] + "-service"
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item
