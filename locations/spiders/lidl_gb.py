import re

import scrapy

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import GeojsonPointItem


class LidlGBSpider(scrapy.Spider):
    name = "lidl_gb"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954"}
    allowed_domains = ["virtualearth.net"]
    base_url = (
        "https://spatial.virtualearth.net/REST/v1/data/588775718a4b4312842f6dffb4428cff/Filialdaten-UK/Filialdaten-UK"
        "?key=Argt0lKZTug_IDWKC5e8MWmasZYNJPRs0btLw62Vnwd7VLxhOxFLW2GfwAhMK5Xg"
        "&$filter=Adresstyp Eq 1"
        "&$select=EntityID,ShownStoreName,AddressLine,Locality,PostalCode,CountryRegion,CityDistrict,Latitude,"
        "Longitude,INFOICON17,OpeningTimes"
        "&$format=json"
    )
    start_urls = [base_url + "&$inlinecount=allpages"]

    def parse(self, response):
        total_count = int(response.json()["d"]["__count"])
        offset = 0
        page_size = 250

        while offset < total_count:
            yield scrapy.Request(
                self.base_url + f"&$top={page_size}&$skip={offset}",
                callback=self.parse_stores,
            )
            offset += page_size

    def parse_stores(self, response):
        stores = response.json()["d"]["results"]

        for store in stores:

            if match := re.match(
                r"(\w{1,2}\d{1,2}\w?) (\d|O)(\w{2})", store["Locality"].upper()
            ):
                if match.group(2) == "O":
                    postcode = match.group(1) + " 0" + match.group(3)
                else:
                    postcode = match.group(1) + " " + match.group(2) + match.group(3)
                city = store["PostalCode"]
            else:
                postcode = store["PostalCode"]
                city = store["Locality"]

            properties = {
                "name": store["ShownStoreName"],
                "ref": store["EntityID"],
                "street_address": store["AddressLine"],
                "city": city,
                "postcode": postcode,
                "country": store["CountryRegion"],
                "addr_full": ", ".join(
                    filter(
                        None,
                        (
                            store["AddressLine"],
                            store["CityDistrict"],
                            city,
                            postcode,
                            "United Kingdom",
                        ),
                    )
                ),
                "lat": float(store["Latitude"]),
                "lon": float(store["Longitude"]),
                "extras": {},
            }

            if store["INFOICON17"] == "customerToilet":
                properties["extras"]["toilets"] = "yes"
                properties["extras"]["toilets:access"] = "customers"

            if matches := re.findall(
                r"(\w{3} ?- ?\w{3}|\w{3}) (\d{2}:\d{2})\*?-(\d{2}:\d{2})",
                store["OpeningTimes"],
            ):
                oh = OpeningHours()
                for rule in matches:
                    day = rule[0]
                    start_time = rule[1]
                    end_time = rule[2]
                    if "-" in day:
                        start_day, end_day = day.split("-")

                        start_day = sanitise_day(start_day)
                        end_day = sanitise_day(end_day)

                        for day in day_range(start_day, end_day):
                            oh.add_range(day, start_time, end_time)
                    else:
                        oh.add_range(day, start_time, end_time)

                properties["opening_hours"] = oh.as_opening_hours()

            yield GeojsonPointItem(**properties)
