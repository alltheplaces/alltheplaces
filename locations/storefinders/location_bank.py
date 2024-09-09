import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

# To use, specify the client ID for the brand in the format of
# StoreLocatorAPI?clientId={client_id}
# You may then need to override the parse_item function to
# adjust extracted field values. In particular, services in
# location["slAttributes"] may be of interest.


class LocationBankSpider(Spider):
    allowed_domains = ["api.locationbank.net"]
    client_id = None
    include_images = False

    def start_requests(self):
        yield JsonRequest(url=f"https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId={self.client_id}")

    def parse(self, response):
        data = response.json()

        if data["detailViewUrl"] is not None:
            # It looks like it is possibble to have a different key, but it does not appear to be used
            detail_view_key = re.search("{(.+)}", data["detailViewUrl"]).group(1)
            if detail_view_key == "locationid":
                detail_view_key = "id"

        for location in data["locations"]:
            location["phone"] = location.pop("primaryPhone")
            if location["additionalPhone1"]:
                location["phone"] += "; " + location.pop("additionalPhone1")
            location["state"] = location.pop("administrativeArea")
            if data["detailViewUrl"] is not None:
                location["website"] = re.sub(r"\{.+\}", location[detail_view_key], data["detailViewUrl"])
            location["street_address"] = clean_address([location.pop("addressLine1"), location.get("addressLine2")])
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
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

            yield from self.parse_item(item, location)

    def parse_item(self, item: Feature, location: dict):
        yield item
