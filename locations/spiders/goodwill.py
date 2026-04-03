import re
from typing import Any
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations

CATEGORY_MAPPING = {
    "1": "Donation Site",
    "2": "Outlet",
    "3": "Retail Store",
    "4": "Job & Career Support",
    "5": "Headquarters",
    "6": "Staffing Services",
    "7": "Specialty Retail",
}


class GoodwillSpider(Spider):
    name = "goodwill"
    item_attributes = {
        "brand": "Goodwill",
        "brand_wikidata": "Q5583655",
        "nsi_id": "-1",
    }
    allowed_domains = ["www.goodwill.org"]

    async def start(self):
        yield Request(url="https://www.goodwill.org/locator/", callback=self.parse_locator)

    def parse_locator(self, response: Response):
        nonce_match = re.search(r'gwlfGlobal[^;]*?"nonce"\s*:\s*"([^"]+)"', response.text)
        if not nonce_match:
            self.logger.error("Could not extract gwlfGlobal.nonce from locator page")
            return
        nonce = nonce_match.group(1)

        for latitude, longitude in point_locations("us_centroids_100mile_radius.csv"):
            # Appears to be a silent limit of 1000 mile radius
            # But any value larger than 200 seems to cause 500 errors
            params = {
                "action": "gwlf_get_locations",
                "security": nonce,
                "radius": "200",
                "lat": latitude,
                "lng": longitude,
                "cats": "1,2,3,4,5",
            }

            yield JsonRequest(url="https://www.goodwill.org/wp-admin/admin-ajax.php?" + urlencode(params))

    def parse(self, response: Response, **kwargs: Any) -> Any:
        response_json = response.json()
        if not response_json.get("success") or not (data := response_json.get("data", {})).get("success"):
            return

        for store in data.get("data", []):
            item = DictParser.parse(store)

            item["name"] = self.item_attributes["brand"]
            item["street_address"] = store.get("LocationStreetAddress1")
            item["city"] = store.get("LocationCity1")
            item["state"] = store.get("LocationState1")
            item["postcode"] = store.get("LocationPostal1")
            item["phone"] = store.get("LocationPhoneOffice")
            item["lat"] = store.get("LocationLatitude1")
            item["lon"] = store.get("LocationLongitude1")

            item["operator"] = store.get("Name_Parent")
            item["extras"]["operator:phone"] = store.get("Phone_Parent")
            item["extras"]["operator:website"] = store.get("LocationParentWebsite")
            item["extras"]["operator:facebook"] = store.get("LocationParentURLFacebook")
            item["extras"]["operator:twitter"] = store.get("LocationParentURLTwitter")

            item["extras"]["store_categories"] = store.get("calcd_ServicesOffered")

            apply_category(Categories.SHOP_CHARITY, item)

            yield item
