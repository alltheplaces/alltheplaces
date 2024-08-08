import base64
import csv
from urllib.parse import urlencode

import scrapy

from locations.categories import Categories
from locations.items import Feature
from locations.searchable_points import open_searchable_points

CATEGORY_MAPPING = {
    "1": "Donation Site",
    "2": "Outlet",
    "3": "Retail Store",
    "4": "Job & Career Support",
    "5": "Headquarters",
}


def b64_wrap(obj) -> str:
    return base64.b64encode(str(obj).encode()).decode()


class GoodwillSpider(scrapy.Spider):
    name = "goodwill"
    item_attributes = {
        "brand": "Goodwill",
        "brand_wikidata": "Q5583655",
        "nsi_id": "-1",
        "extras": Categories.SHOP_CHARITY.value,
    }
    allowed_domains = ["www.goodwill.org"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    download_delay = 0.2

    def start_requests(self):
        with open_searchable_points("us_centroids_25mile_radius.csv") as points:
            reader = csv.DictReader(points)
            for point in reader:
                # Unable to find a way to specify a search radius
                # Appears to use a set search radius somewhere > 25mi, using 25mi to be safe
                params = {
                    "lat": point["latitude"],
                    "lng": point["longitude"],
                    "cats": "3,1,2,4,5",  # Includes donation sites
                }

                url = "https://www.goodwill.org/GetLocAPI.php?" + urlencode(params)
                yield scrapy.Request(url=url)

    def parse(self, response):
        for store in response.json():
            properties = {
                "name": store["LocationName"],
                "ref": store["LocationId"],
                "street_address": store["LocationStreetAddress1"],
                "city": store["LocationCity1"],
                "state": store["LocationState1"],
                "postcode": store["LocationPostal1"],
                "phone": store.get("LocationPhoneOffice"),
                "lat": store.get("LocationLatitude1"),
                "lon": store.get("LocationLongitude1"),
                "website": f'https://www.goodwill.org/locator/location/?store={b64_wrap(store["LocationId"])}&lat={b64_wrap(store["LocationLatitude1"])}&lng={b64_wrap(store["LocationLongitude1"])}',
                "operator": store.get("Name_Parent"),
                "extras": {
                    "store_categories": store.get("calcd_ServicesOffered"),
                    "operator:website": store.get("LocationParentWebsite"),
                    "operator:phone": store.get("Phone_Parent"),
                    "operator:facebook": store.get("LocationParentURLFacebook"),
                    "operator:twitter": store.get("LocationParentURLTwitter"),
                },
            }

            yield Feature(**properties)
