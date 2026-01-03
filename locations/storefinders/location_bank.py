import re
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class LocationBankSpider(Spider):
    """
    To use, specify the client_id attribute for the brand as observed in API
    requests containing:
      StoreLocatorAPI?clientId={client_id}

    You may need to override the parse_item function to adjust extracted field
    values. In particular, services in location["slAttributes"] may be of
    interest.

    Set the include_images attribute to True if the brand provides images of
    each feature in the storefinder. By default, include_images is False.
    """

    dataset_attributes: dict = {"source": "api", "api": "api.locationbank.net"}
    allowed_domains: list[str] = ["api.locationbank.net"]
    client_id: str
    include_images: bool = False

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=f"https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId={self.client_id}")

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        data = response.json()

        if data["detailViewUrl"] is not None:
            # It looks like it is possible to have a different key, but it does not appear to be used.
            detail_view_keys = re.search("{(.+)}", data["detailViewUrl"])
            if detail_view_keys and len(detail_view_keys.groups()) == 1:
                detail_view_key = detail_view_keys.group(1)
            if detail_view_key == "locationid":
                detail_view_key = "id"

        for location in data["locations"]:
            self.pre_process_data(location)
            location["phone"] = location.pop("primaryPhone")
            if location["additionalPhone1"]:
                location["phone"] += "; " + location.pop("additionalPhone1")
            location["state"] = location.pop("administrativeArea")
            if data["detailViewUrl"] is not None:
                location["website"] = re.sub(r"\{.+\}", location[detail_view_key], data["detailViewUrl"])

            location["street_address"] = clean_address([location.pop("addressLine1"), location.get("addressLine2")])

            item = DictParser.parse(location)
            if attribs := getattr(self, "item_attributes", None):
                if isinstance(attribs, dict):
                    if brand_name := attribs.get("brand"):
                        item["branch"] = item.pop("name").replace(brand_name, "").strip()

            item["addr_full"] = clean_address(
                [
                    location.get("street_address"),
                    location.get("subLocality"),
                    location.get("locality"),
                    location.get("state"),
                    location.get("postalCode"),
                ]
            )

            item["opening_hours"] = OpeningHours()
            for day in location["regularHours"]:
                if day["isOpen"]:
                    item["opening_hours"].add_range(day["openDay"], day["openTime"], day["closeTime"])
                else:
                    item["opening_hours"].set_closed(day["openDay"])

            if self.include_images:
                image_root = "https://api.locationbank.net/storelocator/StoreLocatorAPI/locationImage"
                item["image"] = (
                    f"{image_root}?clientId={self.client_id}&LocationID={location['id']}&MediaCat={data['imagesCategory']}&Rule={data['imagesCategorySelectOnRule']}"
                )

            # There are also individual store pages that may have more detail, but nothing of interest has been seen yet,
            # so that is being left unimplemented for now:
            # f"https://api.locationbank.net/storelocator/StoreLocatorAPI/locationDetails?LocationID={location['id']}&ClientID={self.client_id}"

            yield from self.post_process_item(item, response, location)

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the data"""

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        """Override with any post process on the item"""
        yield item
