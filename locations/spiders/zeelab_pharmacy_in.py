from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ZeelabPharmacyINSpider(Spider):
    name = "zeelab_pharmacy_in"
    item_attributes = {"brand": "Zeelab Pharmacy", "brand_wikidata": "Q123015627"}
    no_refs = True

    def make_requests(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://app.zeelabgeneric.com/api/query/stores/web",
            data={"query": "", "page_id": page},
            cb_kwargs={"page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_requests(1)

    def parse(self, response, **kwargs):
        if stores := response.json().get("response_obj"):
            for store in stores:
                store["street_address"] = store.pop("address", "")
                item = DictParser.parse(store)
                item["branch"] = (
                    item.pop("name")
                    .replace("ZEELAB Pharmacy ", "")
                    .replace("Zeelab Pharmacy ", "")
                    .lstrip()
                    .replace("-", "")
                    .lstrip()
                )
                item["phone"] = store.get("contact")
                item["postcode"] = store.get("pincode")
                item["website"] = "https://zeelabpharmacy.com/store-locator"
                apply_category(Categories.PHARMACY, item)
                yield item
            yield self.make_requests(kwargs["page"] + 1)
