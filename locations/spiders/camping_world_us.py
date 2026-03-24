from typing import AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Request

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

GRAPHQL_QUERY = """query ClosestDealers($zipCode: String, $take: Int, $radius: Int, $hours: Boolean, $lat: Float, $long: Float, $standAlone: Boolean) {
  closestDealers(lat: $lat, long: $long, zipCode: $zipCode, take: $take, radius: $radius, hours: $hours, standAlone: $standAlone) {
    closestDealer {
      billingcity
      billingstreet
      marketing_name__c
      billingstatecode
      billingpostalcode
      gl__c
      dealer_url
      long
      lat
      hours {
        department
        mondayClose mondayOpen
        tuesdayClose tuesdayOpen
        wednesdayClose wednesdayOpen
        thursdayClose thursdayOpen
        fridayClose fridayOpen
        saturdayClose saturdayOpen
        sundayClose sundayOpen
      }
      phone
    }
  }
}"""


class CampingWorldUSSpider(scrapy.Spider):
    name = "camping_world_us"
    item_attributes = {"brand": "Camping World", "brand_wikidata": "Q5028383"}

    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        yield JsonRequest(
            url="https://gapi.campingworld.com/",
            data={
                "operationName": "ClosestDealers",
                "variables": {
                    "zipCode": "66952",
                    "take": 2000,
                    "radius": 999999,
                    "hours": True,
                    "lat": 39.7837,
                    "long": -99.3248,
                    "standAlone": True,
                },
                "query": GRAPHQL_QUERY,
            },
        )

    def parse(self, response):
        for store in response.json()["data"]["closestDealers"]["closestDealer"]:
            item = Feature()
            item["lat"] = store["lat"]
            item["lon"] = store["long"]
            item["name"] = store["marketing_name__c"]
            item["ref"] = store["gl__c"]
            item["street_address"] = store["billingstreet"]
            item["postcode"] = store["billingpostalcode"]
            item["city"] = store["billingcity"]
            item["state"] = store["billingstatecode"]
            item["country"] = "US"
            item["phone"] = store["phone"]
            item["website"] = f"https://rv.campingworld.com/dealer/{store['dealer_url']}"
            item["opening_hours"] = self.parse_hours(store.get("hours") or [])
            yield item

    def parse_hours(self, hours_list: list) -> OpeningHours | None:
        oh = OpeningHours()
        sales_hours = next((h for h in hours_list if h.get("department") == "Sales"), None)
        if not sales_hours:
            return None
        try:
            for day_name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                open_time = sales_hours.get(f"{day_name.lower()}Open")
                close_time = sales_hours.get(f"{day_name.lower()}Close")
                if open_time and close_time:
                    oh.add_range(DAYS_EN[day_name], open_time, close_time, "%I:%M %p")
        except Exception:
            return None
        return oh
