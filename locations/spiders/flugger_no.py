from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class FluggerNOSpider(Spider):
    name = "flugger_no"
    allowed_domains = ["api.flugger.no"]
    item_attributes = {"name": "Flügger farve", "brand": "Flügger", "brand_wikidata": "Q10497241"}

    def _make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://api.flugger.no/stores/b2c?page={page}&loadPrevious=false".format(page=page),
            headers={"X-Catalog-Id": "fluggerno", "X-Forwarded-Host": "www.flugger.no"},
            data={"address": None},
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[Any]:
        yield self._make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().get("result", []):
            address = store.get("address", {})
            contact_information = store.get("contactInformation", {})
            store_id = store.get("id")

            properties = {
                "branch": store.get("name"),
                "street_address": address.get("streetAddress"),
                "city": address.get("city"),
                "postcode": address.get("postalCode"),
                "phone": contact_information.get("phoneNumber"),
                "email": contact_information.get("email"),
                "website": f"https://www.flugger.no/st-{store_id}/",
                "lat": address.get("latitude"),
                "lon": address.get("longitude"),
                "ref": store_id,
            }
            apply_category(Categories.SHOP_PAINT, properties)

            try:
                properties["opening_hours"] = self.parse_opening_hours(store.get("openingHours", {}))
            except Exception:
                pass

            yield Feature(**properties)

        if response.json().get("hasNext", False):
            yield self._make_request(response.meta["page"] + 1)

    def parse_opening_hours(self, opening_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, hours in opening_hours.get("weekdays", {}).items():
            if hours["openFrom"] is None and hours["openTo"] is None:
                oh.set_closed(day)
            else:
                oh.add_range(day, hours["openFrom"], hours["openTo"])
        return oh
