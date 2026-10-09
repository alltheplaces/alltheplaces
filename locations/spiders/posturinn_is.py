import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_IS, OpeningHours
from locations.items import Feature


class PosturinnISSpider(Spider):
    name = "posturinn_is"
    item_attributes = {"operator": "Íslandspóstur", "operator_wikidata": "Q291809"}
    allowed_domains = ["api.mobiz.posturinn.is"]
    # Note: in Pósturinn's API a "PostBox" is a parcel locker; letter boxes are /letter-postboxes.

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest("https://api.mobiz.posturinn.is/api/v1/letter-postboxes", callback=self.parse_boxes)
        yield JsonRequest(
            "https://api.mobiz.posturinn.is/api/v1/locations?locationTypes=PostOffice", callback=self.parse_offices
        )

    def parse_boxes(self, response: Response) -> Any:
        for box in response.json():
            item = Feature()
            item["ref"] = box["id"]
            item["lat"], item["lon"] = box["latitude"], box["longitude"]
            item["street_address"] = box.get("address")
            item["postcode"] = str(box.get("postCode") or "")
            item["city"] = box.get("city")
            if box.get("name"):
                item["extras"]["description"] = box["name"]
            apply_category(Categories.POST_BOX, item)
            yield item

    def parse_offices(self, response: Response) -> Any:
        for office in response.json():
            if office.get("notInUse"):
                continue
            item = Feature()
            item["ref"] = office["id"]
            item["branch"] = re.sub(r"^Pósthús\s+", "", office["name"])
            item["lat"], item["lon"] = office["latitude"], office["longitude"]
            address = office.get("address") or {}
            item["street_address"] = address.get("street1")
            item["postcode"] = address.get("postalCode")
            item["city"] = address.get("city")
            item["image"] = office.get("imageURL")
            item["opening_hours"] = self.parse_hours(office.get("statusMessage") or "")
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours:
        # "mán - fim:  9:30-17, fös  9:30-16.", "Mán - fös:  9-12 og 13-17. Samstarfsaðili er Aldan verslun."
        oh = OpeningHours()
        oh.add_ranges_from_string(re.sub(r"\s+og\s+", ", ", text), days=DAYS_IS)
        return oh
