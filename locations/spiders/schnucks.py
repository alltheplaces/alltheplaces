# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class SchnucksSpider(scrapy.Spider):
    name = "schnucks"
    item_attributes = {"brand": "Schnuck's"}
    allowed_domains = ["schnucks.com", "sweetiq.com"]
    start_urls = (
        "https://api.sweetiq.com/store-locator/public/locations/598224b880237d5614a5b7b5?categories=&geo%5B0%5D=-122.2044&geo%5B1%5D=47.7477&tag%5B0%5D=SLS&perPage=3000&page=1&search=&searchFields%5B0%5D=name&box%5B0%5D=-165.71130012499998&box%5B1%5D=-79.42057661509223&box%5B2%5D=1.2808873750000203&box%5B3%5D=73.04134924587599&clientIds%5B0%5D=5931ad931ded45973af8c5c8",
    )

    def store_hours(self, store_hours):
        result = "Mo"
        last_day = "Mo"
        last_period = store_hours["Mon"][0][0] + "-" + store_hours["Mon"][0][1]
        for k in DAYS:

            if len(store_hours[k]):
                period = store_hours[k][0][0] + "-" + store_hours[k][0][1]
                if period == last_period:
                    continue
                if DAYS[DAYS.index(k) - 1][:2] == last_day:
                    result += " " + last_period + ";"
                else:
                    result += (
                        "-" + DAYS[DAYS.index(k) - 1][:2] + " " + last_period + ";"
                    )
                last_period = period
                last_day = k[:2]
                result += k[:2]
            else:
                if k == "Mo":
                    result = ""
                    last_period = ""
                if last_period:
                    if DAYS[DAYS.index(k) - 1][:2] == last_day:
                        result += " " + last_period + ";"
                    else:
                        result += (
                            "-" + DAYS[DAYS.index(k) - 1][:2] + " " + last_period + ";"
                        )
                last_period = ""
                last_day = ""

        if last_day != "Su" and last_period != "":
            result += "-Su"

        result += " " + last_period
        return result

    def parse(self, response):
        shops = json.loads(response.text)
        for shop in shops["records"]:
            yield GeojsonPointItem(
                website=shop["website"],
                ref=shop["name"],
                opening_hours=self.store_hours(shop["hoursOfOperation"]),
                phone=shop["phone"],
                addr_full=shop["address"],
                postcode=shop["postalCode"],
                city=shop["city"],
                state=shop["province"],
                country=shop["country"],
                lat=shop["geo"][1],
                lon=shop["geo"][0],
            )
