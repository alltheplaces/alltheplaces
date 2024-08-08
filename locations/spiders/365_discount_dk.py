from typing import Any, Iterable

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.items import Feature


class ThreehundredsixtyfiveDiscountDKSpider(Spider):
    name = "365_discount_dk"
    item_attributes = {"brand": "365discount", "brand_wikidata": "Q104671354"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        yield FormRequest(
            "https://365discount.coop.dk/umbraco/api/Chains/GetAllStores",
            formdata={"pageId": "4976", "chainsToShowStoresFrom": "Coop 365", "hideClosedStores": "false"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["name"] = location["Name"]
            item["street_address"] = location["Address"]
            item["city"] = location["City"]
            item["postcode"] = str(location["Zipcode"])
            item["lon"], item["lat"] = location["Location"]
            item["phone"] = location["PhoneNumber"]
            item["ref"] = item["website"] = "https://365discount.coop.dk/find-butik/{}".format(location["UrlName"])

            yield item
