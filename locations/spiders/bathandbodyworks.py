# -*- coding: utf-8 -*-
import scrapy
import hashlib
import re
import random

from locations.items import GeojsonPointItem

day_formats = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}

# This spider scrapes both the US locations, as well as the global locations for bathandbodyworks.
class BathAndBodyWorksSpider(scrapy.Spider):
    name = "bathandbodyworks"
    item_attributes = {"brand": "Bath And Body Works"}
    allowed_domains = ["bathandbodyworks.com"]
    start_urls = (
        "https://www.bathandbodyworks.com/on/demandware.store/Sites-BathAndBodyWorks-Site/en_US/Stores-GetNearestStores?latitude=45&longitude=-120&countryCode=US&distanceUnit=mi&maxdistance=25000&BBW=1",
        "https://bathandbodyworks.com/global-locations/global-locations.html",
    )

    # start_requests is overridden so that it starts scraping both sources.
    def start_requests(self):
        return [
            scrapy.Request(
                self.start_urls[0], callback=self.parse_us, dont_filter=True
            ),
            scrapy.Request(
                self.start_urls[1], callback=self.parse_global, dont_filter=True
            ),
        ]

    # This store_hours function was adapted from the one in cookout.py
    def store_hours(self, store_hours):
        days = store_hours.split("<br>")
        days = days[:-1]
        m = []
        for day in days:
            d_split = day.split(": ")
            d_split[0] = day_formats[d_split[0]]
            m.append((d_split[0], d_split[1]))
            # Now we have something like: ("Mo", "10AM-9PM")
            #                         OR: ("Mo", "10:30AM-9:30PM")

        day_groups = []
        this_day_group = dict()
        for day, hours_together in m:
            if hours_together == "CLOSED":
                continue

            hours_apart = hours_together.split("-")
            from_ = hours_apart[0]
            to_ = hours_apart[1]

            if ":" in from_:
                (from_h, from_m, from_ap) = re.findall(
                    "([0-9]{1,2}):([0-9]{1,2})([APM]{2})", from_
                )[0]
            else:
                (from_h, from_ap) = re.findall("([0-9]{1,2})([APM]{2})", from_)[0]
                from_m = "00"

            if ":" in to_:
                (to_h, to_m, to_ap) = re.findall(
                    "([0-9]{1,2}):([0-9]{1,2})([APM]{2})", to_
                )[0]
            else:
                (to_h, to_ap) = re.findall("([0-9]{1,2})([APM]{2})", to_)[0]
                to_m = "00"

            from_h = int(from_h)
            if from_ap == "PM" and (from_h != 12):
                from_h += 12

            to_h = int(to_h)
            if to_ap == "PM" and (to_h != 12):
                to_h += 12

            hours = "{:02}:{}-{:02}:{}".format(
                from_h,
                from_m,
                to_h,
                to_m,
            )

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

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
                elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse_global(self, response):
        for country in response.xpath('//a[contains(@class, "country-label")]'):
            country_url = country.xpath("@href").extract_first()
            country_name = country.xpath("text()").extract_first()
            yield scrapy.Request(
                country_url,
                callback=self.parse_global_country,
                meta={"country_name": country_name},
            )

    def parse_global_country(self, response):
        stores = response.xpath('//div[@class="store-location"]')
        for store in stores:
            properties = {}
            country_name = response.meta.get("country_name")
            name = store.xpath('.//p[@class="store-name"]/text()').extract_first()
            citystate = store.xpath('.//p[@class="location"]/text()').extract_first()
            location = store.xpath(
                'string(.//p[text()="Location"]/following-sibling::p)'
            ).extract_first()
            phone = store.xpath(
                './/p[text()="Phone Number"]/following-sibling::p/text()'
            ).extract_first()

            properties["country"] = country_name
            if name:
                properties["name"] = name
            if citystate:
                if ", " in citystate:
                    city, state = citystate.split(", ")
                    properties["city"] = city
                else:
                    state = citystate

                if country_name not in state.title():
                    properties["state"] = state

            if location:
                properties["addr_full"] = location
            if phone and ("TBD" not in phone):
                properties["phone"] = phone

            # We aren't given a ref for these, so generate one based on a few
            # of the available properties that are likely to be unique.
            ref_input = ""
            for key in ["name", "phone", "location"]:
                if key in properties:
                    try:
                        ref_input += properties[key].encode("utf-8")
                    except TypeError:
                        ref_input += properties[key]

            properties["ref"] = hashlib.md5(ref_input.encode("utf-8")).hexdigest()

            yield GeojsonPointItem(**properties)

    def parse_us(self, response):
        results = response.json()
        stores = results["stores"]

        for store_key in stores:
            store_data = stores[store_key]

            properties = {
                "name": store_data["name"],
                "phone": store_data["phone"],
                "addr_full": store_data["address1"].title(),
                "city": store_data["city"].title(),
                "state": store_data["stateCode"],
                "postcode": store_data["postalCode"],
                "country": store_data["countryCode"],
                "lon": float(store_data["longitude"]),
                "lat": float(store_data["latitude"]),
                "ref": store_key,
            }

            hours = store_data["storeHours"] if "storeHours" in store_data else None
            opening_hours = None
            if hours and ("Please call" not in hours):
                try:
                    opening_hours = self.store_hours(hours)
                except:
                    pass
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
