import json

from scrapy import Request
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class DiscountTireSpider(SitemapSpider):
    name = "discount_tire"
    item_attributes = {"brand": "Discount Tire", "brand_wikidata": "Q5281735"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    sitemap_urls = ["https://sitemaps.discounttire.com/store.xml"]

    def parse(self, response, **kwargs):
        yield Request(
            url="https://www.discounttire.com/webapi/discounttire.graph",
            method="POST",
            body=json.dumps(
                {
                    "operationName": "StoreByCode",
                    "variables": {"storeCode": str(response.url.split("/")[-1])},
                    "query": "query StoreByCode($storeCode: String!) {\n  store {\n    byCode(storeCode: $storeCode) {\n      ...myStoreFields\n    }\n  }\n}\n\nfragment myStoreFields on StoreData {\n  code\n  applicationType\n  address {\n    country {\n      isocode\n      name\n    }\n    email\n    line1\n    line2\n    phone\n    postalCode\n    region {\n      isocodeShort\n      name\n    }\n    town\n  }\n  additionalServices {\n    name\n    link\n    code\n  }\n  remainingWinterDays\n  winterStore\n  baseStore\n  pitPass\n  description\n  displayName\n  isBopisTurnedOff: bopisTurnedOff\n  distance\n  legacyStoreCode\n  geoPoint {\n    latitude\n    longitude\n  }\n  rating {\n    rating\n    numberOfReviews\n  }\n  weekDays {\n    closed\n    closingTime {\n      formattedHour\n      hour\n      minute\n    }\n    formattedDate\n    openingTime {\n      formattedHour\n      hour\n      minute\n    }\n    dayOfWeek\n  }\n  nearByStores {\n    code\n    distance\n    address {\n      line1\n    }\n    pitPass\n  }\n}\n",
                }
            ),
            callback=self.parse_store,
            cb_kwargs={"url": response.url},
        )

    def parse_store(self, response, url):
        poi = response.json()["data"]["store"]["byCode"]
        item = DictParser.parse(poi)
        item["website"] = url
        item["ref"] = poi.get("code")
        if line2 := poi.get("address", {}).get("line2"):
            item["street_address"] = item["street_address"] + " " + line2
        item["phone"] = poi.get("address", {}).get("phone")
        item["email"] = poi.get("address", {}).get("email")
        item["state"] = poi.get("address", {}).get("region", {}).get("name")
        self.parse_hours(item, poi.get("weekDays", []))

        yield item

    def parse_hours(self, item, week_days):
        try:
            oh = OpeningHours()
            for day in week_days:
                if day.get("closed"):
                    continue
                opening_time = day.get("openingTime", {})
                closing_time = day.get("closingTime", {})
                oh.add_range(
                    DAYS_EN[day.get("dayOfWeek").capitalize()],
                    opening_time.get("formattedHour"),
                    closing_time.get("formattedHour"),
                    "%H:%M %p",
                )
            item["opening_hours"] = oh.as_opening_hours()
        except Exception:
            pass
