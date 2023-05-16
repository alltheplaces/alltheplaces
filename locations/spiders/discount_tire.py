import json
import re

import scrapy
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

URL = "https://data.discounttire.com/webapi/discounttire.graph"


class DiscountTireSpider(SitemapSpider):
    name = "discount_tire"
    item_attributes = {"brand": "Discount Tire", "brand_wikidata": "Q5281735"}
    allowed_domains = ["discounttire.com"]
    sitemap_urls = [
        "https://www.discounttire.com/sitemap.xml",
    ]
    sitemap_follow = [
        r".*Discount-Tire-Sitemap-Categories-Content.*\.xml",
    ]
    sitemap_rules = [
        (
            r"^https://www.discounttire.com/store/.*",
            "parse_site",
        )
    ]
    download_delay = 5.0
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def parse_site(self, response):
        store_code = re.search(r".*/s/(\d*)$", response.url).group(1)
        payload = {
            "operationName": "StoreByCode",
            "variables": {"storeCode": f"{store_code}"},
            "query": "query StoreByCode($storeCode: String!) {\n  store {\n    byCode(storeCode: $storeCode) {\n      ...myStoreFields\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment myStoreFields on StoreData {\n  code\n  address {\n    country {\n      isocode\n      name\n      __typename\n    }\n    email\n    line1\n    line2\n    phone\n    postalCode\n    region {\n      isocodeShort\n      name\n      __typename\n    }\n    town\n    __typename\n  }\n  winterStore\n  baseStore\n  description\n  displayName\n  isBopisTurnedOff: bopisTurnedOff\n  distance\n  legacyStoreCode\n  geoPoint {\n    latitude\n    longitude\n    __typename\n  }\n  rating {\n    rating\n    numberOfReviews\n    __typename\n  }\n  weekDays {\n    closed\n    formattedDate\n    dayOfWeek\n    __typename\n  }\n  __typename\n}\n",
        }

        yield scrapy.Request(
            url=URL,
            method="POST",
            body=json.dumps(payload),
            callback=self.parse_stores,
            meta={"website": response.url},
        )

    def parse_stores(self, response):
        store_data = json.loads(response.text)
        data = store_data["data"]["store"]["byCode"]

        if data:
            properties = {
                "name": data["displayName"],
                "ref": data["code"],
                "street_address": data["address"]["line1"],
                "city": data["address"]["town"],
                "state": data["address"]["region"]["isocodeShort"],
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["country"]["isocode"],
                "phone": data["address"].get("phone"),
                "website": response.meta.get("website"),
                "lat": float(data["geoPoint"]["latitude"]),
                "lon": float(data["geoPoint"]["longitude"]),
            }

            yield Feature(**properties)
