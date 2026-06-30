import json
import re
from typing import Any, AsyncIterator, Iterable
from urllib.parse import urlencode

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS

CATEGORY_MAPPING = {
    "1": "Donation Site",
    "2": "Outlet",
    "3": "Retail Store",
    "4": "Job & Career Support",
    "5": "Headquarters",
    "6": "Staffing Services",
    "7": "Specialty Retail",
}


class GoodwillSpider(PlaywrightSpider):
    name = "goodwill"
    item_attributes = {"brand": "Goodwill", "brand_wikidata": "Q5583655", "nsi_id": "-1"}
    allowed_domains = ["www.goodwill.org"]
    # admin-ajax.php returns 403 to direct requests, so the calls
    # are made from inside the browser below. Let those through the default
    # "abort everything but documents" rule.
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "PLAYWRIGHT_ABORT_REQUEST": lambda r: r.resource_type != "document" and "admin-ajax.php" not in r.url
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.goodwill.org/locator/",
            meta={"playwright": True, "playwright_include_page": True},
            callback=self.parse_locator,
        )

    async def parse_locator(self, response: Response) -> AsyncIterator[Feature]:
        page = response.meta["playwright_page"]
        try:
            for latitude, longitude in point_locations("us_centroids_100mile_radius.csv"):
                # Appears to be a silent limit of 1000 mile radius
                # But any value larger than 200 seems to cause 500 errors
                params = {
                    "action": "gwlf_get_locations",
                    "security": re.search(r'gwlfGlobal[^;]*?"nonce"\s*:\s*"([^"]+)"', response.text).group(1),
                    "radius": "200",
                    "lat": latitude,
                    "lng": longitude,
                    "cats": "1,2,3,4,5",
                }
                url = "https://www.goodwill.org/wp-admin/admin-ajax.php?" + urlencode(params)
                # Fetch from inside the browser so the request carries the page's cookies and origin.
                for item in self.parse(await page.evaluate("(url) => fetch(url).then((r) => r.text())", url)):
                    yield item
        finally:
            await page.close()

    def parse(self, body: str, **kwargs: Any) -> Iterable[Feature]:
        response_json = json.loads(body)
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
