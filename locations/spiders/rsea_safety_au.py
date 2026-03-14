from typing import AsyncIterator

from scrapy import Selector, Spider
from scrapy.http import FormRequest, Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class RseaSafetyAUSpider(Spider):
    name = "rsea_safety_au"
    item_attributes = {
        "brand": "RSEA Safety",
        "brand_wikidata": "Q122418895",
    }
    allowed_domains = ["www.rsea.com.au"]
    start_urls = ["https://www.rsea.com.au/service/storeLocator/findNearestStore"]
    custom_settings = {"COOKIES_ENABLED": True}

    async def start(self) -> AsyncIterator[Request]:
        # A session cookie first needs to be obtained.
        yield Request(url="https://www.rsea.com.au/store-locator", callback=self.request_location_data)

    def request_location_data(self, response):
        formdata = {
            "_applicationType": "cssnet",
            "_sessionId": "guestuser00000000-0000-0000-0000-000000000000",
            "checkStoreAvailabilityClickAndCollect": "false",
            "featureFilter": "",
            "filters": "",
            "jsonFieldGroupName": "",
            "latitude": "0",
            "longitude": "0",
            "maxStores": "0",
        }
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-Requested-CV": "_token",
        }
        for url in self.start_urls:
            yield FormRequest(url=url, formdata=formdata, headers=headers, method="POST")

    def parse(self, response):
        for location in response.json()["data"]:
            if not location.get("IsActive"):
                continue
            item = DictParser.parse(location)
            item["ref"] = location["WarehouseCode"]
            item["street_address"] = clean_address([location.get("AddressLine1"), location.get("AddressLine2")])
            item["website"] = (
                "https://www.rsea.com.au/store-locator/"
                + location["State"].lower()
                + "/"
                + location["Suburb"].lower().replace(" ", "-")
            )
            hours_string = " ".join(Selector(text=location["OpeningHoursHTML"]).xpath("//text()").getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            apply_category(Categories.SHOP_SAFETY_EQUIPMENT, item)
            yield item
