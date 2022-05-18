# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class NextSpider(scrapy.Spider):
    name = "next_uk"
    item_attributes = {"brand": "Next", "brand_wikidata": "Q246655"}
    allowed_domains = ["next.co.uk"]
    start_urls = ("http://stores.next.co.uk/",)

    def store_hours(self, store_hours):
        o = OpeningHours()

        for day in DAYS:
            open_time, close_time = store_hours[day].split("-")
            open_time = open_time.rstrip()
            close_time = close_time.rstrip()
            if (len(open_time) < 3 or len(open_time) > 4) and (
                len(close_time) < 3 or len(close_time) > 4
            ):
                pass
            else:
                o.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H%M",
                )

        return o.as_opening_hours()

    def parse(self, response):
        countries = response.xpath('//select[@id="country-store"]/option/@value')
        for country in countries:
            req = {"country": country.extract()}
            yield scrapy.FormRequest(
                "https://stores.next.co.uk/index/stores",
                formdata=req,
                method="POST",
                callback=self.parse_city,
            )

    def parse_city(self, response):
        cities = response.xpath("//option/@value")
        for city in cities:
            yield scrapy.Request(
                "http://stores.next.co.uk/stores/single/" + city.extract(),
                callback=self.parse_shop,
            )

    def parse_shop(self, response):
        text = response.xpath(
            '//script[contains(.,"window.lctr.single_search")]/text()'
        ).extract_first()
        parts = text.split("window.lctr.results.push(")

        for place in range(1, 2):
            shop = json.loads(parts[place].strip().rstrip(";").rstrip(")"))
            try:
                hours = self.store_hours(
                    {
                        "Mo": shop["mon_open"] + "-" + shop["mon_close"],
                        "Tu": shop["tues_open"] + "-" + shop["tues_close"],
                        "We": shop["weds_open"] + "-" + shop["weds_close"],
                        "Th": shop["thurs_open"] + "-" + shop["thurs_close"],
                        "Fr": shop["fri_open"] + "-" + shop["fri_close"],
                        "Sa": shop["sat_open"] + "-" + shop["sat_close"],
                        "Su": shop["sun_open"] + "-" + shop["sun_close"],
                    }
                )
            except Exception:
                hours = ""

            properties = {
                "ref": shop["location_id"],
                "name": shop["branch_name"],
                "addr_full": shop["AddressLine"] + "," + shop["street"],
                "city": shop["city"],
                "country": shop["country"],
                "lat": float(shop["Latitude"]),
                "lon": float(shop["Longitude"]),
                "phone": shop["telephone"],
                "website": response.url,
            }

            if hours:
                properties["opening_hours"] = hours
            if shop["PostalCode"]:
                properties["postcode"] = shop["PostalCode"]
            if shop["county"]:
                properties["state"] = shop["county"]

            if shop["AddressLine"] and shop["centre"] and shop["street"]:
                properties["addr_full"] = (
                    shop["AddressLine"] + ", " + shop["centre"] + ", " + shop["street"]
                )
            elif shop["street"] and shop["centre"]:
                properties["addr_full"] = shop["centre"] + "," + shop["street"]
            elif shop["AddressLine"] and shop["centre"]:
                properties["addr_full"] = shop["AddressLine"] + ", " + shop["centre"]
            elif shop["street"]:
                properties["addr_full"] = shop["street"]
            elif shop["centre"]:
                properties["addr_full"] = shop["centre"]
            elif shop["AddressLine"]:
                properties["addr_full"] = shop["AddressLine"]
            elif shop["town"]:
                properties["addr_full"] = shop["town"]
            else:
                properties["addr_full"] = ""

            yield GeojsonPointItem(**properties)
