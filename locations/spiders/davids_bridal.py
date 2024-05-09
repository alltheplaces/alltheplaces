from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class DavidsBridalSpider(Spider):
    name = "davids_bridal"
    item_attributes = {"brand": "Davids Bridal", "brand_wikidata": "Q5230388"}
    allowed_domains = ["www.davidsbridal.com"]
    start_urls = ["https://www.davidsbridal.com/api/graphql"]

    def start_requests(self):
        for url in self.start_urls:
            data = {
                "query": """
query getStoreLocatorList {
    storeLocationList(active: true) {
        ...StoreLocatorFragment
        ...StoreLocatorMessagingFragment
        ...StoreLocatorHoursFragment
    }
}

fragment StoreLocatorFragment on StoreLocation {
    active
    name
    phone
    storeId
    appointmentsEligible
    storeType
    timezone
    location {
        postalCode
        state
        city
        country
        countryCode
        latitude
        longitude
        address1
        address2
        building
    }
}

fragment StoreLocatorMessagingFragment on StoreLocation {
    messaging {
        lines {
            text
        }
    }
}

fragment StoreLocatorHoursFragment on StoreLocation {
    hours {
        regular {
            close
            day
            open
        }
        override {
            date
            end
            name
            start
            timeType
        }
    }
}
""",
                "operationName": "getStoreLocatorList",
                "variables": {},
            }
        yield JsonRequest(url=url, data=data)

    def parse(self, response):
        for data in response.json().get("data", {}).get("storeLocationList"):
            item = DictParser.parse(data)
            item["postcode"] = data.get("location", {}).get("postalCode")
            item["state"] = data.get("location", {}).get("state")
            item["city"] = data.get("location", {}).get("city")
            item["street_address"] = clean_address(
                [data.get("location", {}).get("address1"), data.get("location", {}).get("address2")]
            )
            if item["postcode"] and item["state"]:
                item["website"] = (
                    f'https://www.davidsbridal.com/stores/{item["city"].lower()}-{item["state"].lower()}-{item["postcode"].lower().replace(" ", "").replace("-", "")}-{item["ref"]}'
                )
            item["opening_hours"] = OpeningHours()
            if data.get("hours", {}):
                for day in data.get("hours", {}).get("regular"):
                    item["opening_hours"].add_range(
                        day=day.get("day"), open_time=day.get("open")[:5], close_time=day.get("close")[:5]
                    )
            yield item
