# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem

STATES = [
    "AL",
    "AK",
    "AS",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FM",
    "FL",
    "GA",
    "GU",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MH",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "MP",
    "OH",
    "OK",
    "OR",
    "PW",
    "PA",
    "PR",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VI",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]


class BostonMarketSpider(scrapy.Spider):
    name = "boston_market"
    item_attributes = {"brand": "Boston Market"}
    allowed_domains = ["www.bostonmarket.com"]
    base_url = "https://www.bostonmarket.com"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for state in STATES:
            yield scrapy.Request(
                "https://www.bostonmarket.com/wp-admin/admin-ajax.php?"
                "action=bingmaps_locations_search_ajax&search={}".format(state)
            )

    def store_hours(self, store_details):
        day_groups = []
        this_day_group = None
        for line in store_details.keys():
            if not line.endswith("Open"):
                continue
            if line.endswith("Open"):
                day = line.rstrip("Open")
                hours = store_details.get(line)
                hours += "-"
                hours += store_details.get(day + "Close")

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

        if this_day_group:
            day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                elif day_group["from_day"] == "Mo" and day_group["to_day"] == "Su":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]
        return opening_hours

    def parse(self, response):
        data = response.json()["locations"]

        for store in data:
            store_details = store["bing"]
            (num, street) = store_details["AddressLine"].split(" ", 1)

            properties = {
                "phone": store_details["Phone"],
                "ref": store_details["EntityID"],
                "name": store["post"]["post_title"],
                "opening_hours": self.store_hours(store_details),
                "lat": store_details["Latitude"],
                "lon": store_details["Longitude"],
                "addr_full": store_details["AddressLine"],
                "housenumber": num,
                "street": street,
                "city": store_details["Locality"],
                "state": store_details["AdminDistrict"],
                "postcode": store_details["PostalCode"],
                "country": store_details["CountryRegion"],
                "website": store["url"],
            }

            yield GeojsonPointItem(**properties)
