# -*- coding: utf-8 -*-
import re

import scrapy

from locations.hours import DAYS_EN
from locations.items import GeojsonPointItem


class Duffys(scrapy.Spider):

    name = "duffys"
    item_attributes = {"brand": "Duffys"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(
            url="https://api.duffysmvp.com/api/app/nearByLocations",
            data={"latitude": "26.6289791", "longitude": "-80.0724384"},
        )

    def parse(self, response):
        results = response.json()

        for store in results:
            address_results = store.get("address")

            oh = store.get("hoursOfOperation")
            oh = [format_hours(o) for o in oh.split(" ")]
            # print(" ".join(m))
            oh = (
                " ".join(oh)
                .replace(",", ";")
                .replace(" - ", "-")
                .replace("Daily", "Mo-Su")
                .lstrip(" ")
            )

            formated = [
                oh_string.replace("am", "").replace("pm", "")
                if re.search(r"\d", oh_string) and len(oh_string) >= 7
                else oh_string.replace("am", ":00").replace("pm", ":00")
                for oh_string in oh.split(" ")
            ]
            for k, v in DAYS_EN.items():
                oh = oh.replace(k, v)

            properties = {
                "ref": store.get("code"),
                "name": store.get("name"),
                "street_address": address_results.get("address1"),
                "city": address_results.get("city"),
                "country": address_results.get("country"),
                "phone": address_results.get("phone"),
                "state": address_results.get("stateProvince"),
                "postcode": address_results.get("postalCode"),
                "opening_hours": oh,
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
            }

            yield GeojsonPointItem(**properties)


def format_hours(oh_string):
    has_comma = "," in oh_string
    oh_string = oh_string.replace(",", "")
    if any(x in oh_string for x in ["am", "pm"]):
        if any(x in oh_string for x in ["pm", "12"]):
            oh_string = oh_string.replace("pm", "").replace("am", "")
            if ":" in oh_string:
                oh_string_s = oh_string.split(":")
                oh_string_h = int(oh_string_s[0]) + 12
                oh_string = (
                    str(oh_string_h) + ":".join(oh_string_s[1:])
                    if oh_string_h < 24
                    else "00:" + "".join(oh_string_s[1:])
                )
            else:
                oh_string_h = int(oh_string) + 12
                oh_string = str(oh_string_h) + ":00" if oh_string_h < 24 else "00:00"
        else:
            oh_string = (
                oh_string.replace("am", "")
                if ":" in oh_string
                else oh_string.replace("am", ":00")
            )
        oh_string = oh_string + "," if has_comma else oh_string
    else:
        return oh_string.replace(":", "")
    return oh_string
