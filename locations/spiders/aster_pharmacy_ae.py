import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

ASTER_PHARMACY = {"brand": "Aster Pharmacy", "brand_wikidata": "Q124453575"}


class AsterPharmacyAESpider(Spider):
    name = "aster_pharmacy_ae"
    no_refs = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest("https://www.asterpharmacy.ae/aster-api/REST/getStore", data={})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = Feature()
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["addr_full"] = location["locationname"]
            item["phone"] = location["mobilenumber"]

            title = " ".join(location["title"].split())
            # The store list also carries pharmacies of other brands.
            if title.lower().startswith(("aster", "apg")):
                item.update(ASTER_PHARMACY)
                item["branch"] = re.sub(r"^Aster Pharmacy (- )?(?=[A-Z])", "", title)
            else:
                item["name"] = title

            # For some stores the city is a copy of the title.
            city = " ".join(location["city"].split())
            if city != title:
                item["city"] = city

            apply_category(Categories.PHARMACY, item)

            yield item
