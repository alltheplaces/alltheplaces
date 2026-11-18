from typing import Any, AsyncIterator, Iterable

from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class PlumblinkNAZASpider(JSONBlobSpider):
    name = "plumblink_na_za"
    item_attributes = {"brand": "Plumblink", "brand_wikidata": "Q127596751"}
    locations_key = "records"

    async def start(self) -> AsyncIterator[Request]:
        yield JsonRequest(
            url="https://api.esolve.co.za/get-access-token.php?anonymous=true&ws_id=PLNK01",
            callback=self.parse_token,
        )

    def parse_token(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url="https://api.esolve.co.za/get-locations.php?is_active=true&ws_id=PLNK01",
            headers={"authorization": response.json()["additional_data"]["key"]},
            callback=self.parse,
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["head_office"] == 1:
            return

        item["branch"] = feature.pop("description", "").removeprefix("Plumblink ")
        identifier = feature.pop("identifier", "")
        item["website"] = "https://www.plumblink.co.za/store/" + identifier if identifier else None

        item["street_address"] = item.pop("street", "")

        item["phone"] = feature.pop("branch_telnumber", "")
        item["email"] = feature.pop("branch_email", "")
        item["extras"]["contact:whatsapp"] = feature.pop("branch_whatsapp_number", "")
        item["extras"]["fax"] = feature.pop("branch_fax", "")

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            open_time = feature.get(f"{day.lower()}_open_time")
            close_time = feature.get(f"{day.lower()}_close_time")
            if open_time == close_time:
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_range(day, open_time, close_time)

        apply_category(Categories.SHOP_HARDWARE, item)

        yield item
