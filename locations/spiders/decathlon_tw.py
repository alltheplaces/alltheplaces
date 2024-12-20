import json
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class DecathlonTWSpider(Spider):
    name = "decathlon_tw"
    item_attributes = {"brand": "Decathlon", "brand_wikidata": "Q509349"}
    start_urls = ["https://www.decathlon.tw/api/store-setting?countryCode=TW"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield Request(
            url="https://www.decathlon.tw/s/門市資訊",
            callback=self.parse_store_details,
            meta=dict(stores=response.json()),
        )

    def parse_store_details(self, response: Response, **kwargs: Any) -> Any:
        store_list_with_extra_info = []
        for obj in json.loads(response.xpath('//*[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"]["content"][
            "floor"
        ]:
            if store_list := obj.get("fields", {}).get("storeList"):
                store_list_with_extra_info.extend(store_list)
        store_pages = {
            store["fields"]["storeId"]: store["fields"]["ctaLink"]
            for store in store_list_with_extra_info
            if store.get("fields")
        }
        for store in response.meta["stores"]:
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["branch"] = item.pop("name").strip("店")
            item["phone"] = store.get("phone1")
            item["website"] = response.urljoin(store_pages.get(store["id"]))
            item["opening_hours"] = OpeningHours()
            for rule in store.get("workingHours", []):
                item["opening_hours"].add_range(DAYS[rule["day"] - 1], rule["open"], rule["close"])
            yield item
