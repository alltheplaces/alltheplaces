from typing import Any, Iterable

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class SingaporePostSGSpider(Spider):
    name = "singapore_post_sg"
    item_attributes = {"brand": "Singapore Post", "brand_wikidata": "Q4049531"}

    def start_requests(self) -> Iterable[Request]:
        # We need to collect cookies, locate-us-type is important
        yield FormRequest(
            url="https://www.singpost.com/locate-us",
            formdata={
                "locate-us-type": "1",
                "keyword": "",
                "place_id": "",
                "op": "Find",
                "form_id": "frontend_locate_us_form",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield response.follow("https://www.singpost.com/locate-us/get-map-data", self.parse_locations)

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data_map"]:
            item = Feature()
            item["ref"] = location["outletId"]
            item["name"] = location["outletName"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["phone"] = location["phoneNumber"]
            item["housenumber"] = location["houseBlockNumber"]
            item["extras"]["addr:housename"] = location["buildingName"]
            item["extras"]["addr:unit"] = location["unitNumber"]
            item["street"] = location["streetName"]
            item["city"] = location["city"]
            item["postcode"] = location["postCode"]
            item["email"] = location["email"]
            item["country"] = location["country"]

            # operatingHours

            if location["outletType"] == "PostOffice":
                apply_category(Categories.POST_OFFICE, item)

            yield item
