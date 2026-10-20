import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ZeelabPharmacyINSpider(Spider):
    name = "zeelab_pharmacy_in"
    item_attributes = {"brand": "Zeelab Pharmacy", "brand_wikidata": "Q123015627"}
    no_refs = True

    def make_requests(self, page: int) -> Request:
        return Request(
            url=f"https://zeelabpharmacy.com/store-location_list?query=&page_id={page}",
            cb_kwargs={"page": page},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_requests(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if stores := response.json().get("response_obj"):
            for store in stores:
                store["street_address"] = store.pop("address", "")
                item = DictParser.parse(store)
                item["branch"] = (
                    re.sub(
                        r"^\s*zeelab\s*(arogya\s*generic\s*)?phar\w*\s*[-,]?\s*",
                        "",
                        item.pop("name"),
                        flags=re.IGNORECASE,
                    ).strip()
                    or None
                )
                item["phone"] = store.get("contact")
                item["postcode"] = store.get("pincode")
                item["website"] = None
                apply_category(Categories.PHARMACY, item)
                yield item
            yield self.make_requests(kwargs["page"] + 1)
