import re

import scrapy

from locations.hours import day_range, OpeningHours, sanitise_day
from locations.items import GeojsonPointItem


class LidlIESpider(scrapy.Spider):
    name = "lidl_ie"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954"}
    allowed_domains = ["virtualearth.net"]
    base_url = (
        "https://spatial.virtualearth.net/REST/v1/data/94c7e19092854548b3be21b155af58a1/Filialdaten-RIE/Filialdaten-RIE"
        "?key=AvlHnuUnvOF2tIm9bTeXIj9T4YvpuerURAEX2uC8YKY3-1Q9cWJpmxVM_tqiduGt"
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
            properties = {
                "name": store["ShownStoreName"],
                "ref": store["EntityID"],
                "street_address": store["AddressLine"],
                "city": store["CityDistrict"],
                "state": store["Locality"],
                "postcode": store["PostalCode"],
                "country": store["CountryRegion"],
                "addr_full": ", ".join(
                    filter(
                        None,
                        (
                            store["AddressLine"],
                            store["CityDistrict"],
                            store["Locality"],
                            store["PostalCode"],
                            "Ireland",
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
                r"(\w+ - \w+|\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
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
                        if day := sanitise_day(day):
                            oh.add_range(day, start_time, end_time)

                properties["opening_hours"] = oh.as_opening_hours()

            yield GeojsonPointItem(**properties)
