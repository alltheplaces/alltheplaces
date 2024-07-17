import json
import re

import scrapy

from locations.items import Feature


class MisterCarWashSpider(scrapy.Spider):
    name = "mister_car_wash"
    item_attributes = {"brand": "Mister Car Wash", "brand_wikidata": "Q114185788"}
    allowed_domains = ["mistercarwash.com/"]
    start_urls = ("http://mistercarwash.com/locations/",)

    def store_hours(self, store_hours):
        if not store_hours or len(store_hours) < 5:
            return

        stri = ""
        for line in store_hours.split(";"):
            match = re.search(
                r"\s*(\d{1,2}):(\d{1,2})\s*(am|pm|mp)?\s*-\s*(\d{1,2}):(\d{1,2})\s*(am|pm|mp)\s*(\w*)(\s*-\s*(\w*))?",
                line,
            )
            stri += match[7][:2]

            try:
                stri += match[8][:3] + " "
            except Exception:
                stri += " "
            stri += str(int(match[1]) + (12 if match[3] in ["pm", "mp"] else 0)) + ":" + match[2] + "-"
            stri += str(int(match[4]) + (12 if match[6] in ["pm", "mp"] else 0)) + ":" + match[5] + ";"

        return stri.rstrip(";")

    def phone_normalize(self, phone):
        r = re.search(
            r"\+?(\s+)*(\d{1})?(\s|\()*(\d{3})(\s+|\))*(\d{3})(\s+|-)?(\d{2})(\s+|-)?(\d{2})",
            phone,
        )
        return ("(" + r.group(4) + ") " + r.group(6) + "-" + r.group(8) + "-" + r.group(10)) if r else phone

    def parse(self, response):  # high-level list of states
        washers_str = response.xpath('//script[contains(.,"markers =")]').extract_first()
        j_beg = washers_str.find("markers =") + 10
        j_end = washers_str.find("\n\t", j_beg)
        wash_list = json.loads(washers_str[j_beg:j_end].strip().rstrip(";"))

        for wash in wash_list:
            address_parts = re.match(
                r"(.*),\s*(\D{2,}\s?\D{2,}?\s?\D*)\s*,\s*(\D{2})\s*(\d{5})?,(\D{4,})?",
                wash["address"],
            )
            if not address_parts:
                address_parts = re.match(r"(.*),\s*(\D{2,}\s?\D{2,}?\s?\D*)\s(\D{2})", wash["address"])
            if not address_parts:
                address_parts = re.match(r"(.*),\s?(\D*)", wash["address"])
            try:
                zip_code = address_parts[4]
            except Exception:
                zip_code = ""
            try:
                state = address_parts[3]
            except Exception:
                state = ""
            try:
                country = address_parts[6].strip()
            except Exception:
                country = "US"

            phone = self.phone_normalize(
                wash["infoContent"][
                    wash["infoContent"].find("<b>Phone:</b>")
                    + 13 : wash["infoContent"].find("/div", wash["infoContent"].find("<b>Phone:</b>"))
                    - 1
                ]
            )

            yield Feature(
                lat=float(wash["lat"]),
                lon=float(wash["lng"]),
                phone=phone,
                website="http://mistercarwash.com/locations/" + wash["name"].lower().replace(" ", "-"),
                ref=wash["loc_id"],
                opening_hours=self.store_hours(wash["loc_hours"]),
                addr_full=address_parts[1],
                city=address_parts[2],
                state=state,
                postcode=zip_code,  # no ZIP information :-(
                country=country,
            )
