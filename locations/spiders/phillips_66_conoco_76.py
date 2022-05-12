# -*- coding: utf-8 -*-
import scrapy
import urllib

from locations.items import GeojsonPointItem

HEADERS = {"Content-Type": "application/json"}

BRANDS = {"U76": "76", "P66": "Phillips 66", "CON": "Conoco"}

WIKIBRANDS = {"U76": "Q1658320", "P66": "Q1656230", "CON": "Q214763"}


class Phillips66Spider(scrapy.Spider):
    name = "phillips_66_conoco_76"
    allowed_domains = ["spatial.virtualearth.net"]
    download_delay = 0.2

    base_url = "https://spatial.virtualearth.net/REST/v1/data/a1ed23772f5f4994a096eaa782d07cfb/US_BrandedSites/Sites?$filter=(Brand%20eq%20%27P66%27%20OR%20Brand%20Eq%20%27U76%27%20OR%20Brand%20Eq%20%27CON%27)&$format=json&$inlinecount=allpages&$select=*,__Distance&key=AvroZVNGVuRnilfbaoMSyXJhjA36NTNr8jdIufcn1erJ_kJMF5UE33M_ENXxHwTb&$top=250"

    def start_requests(self):
        yield scrapy.Request(self.base_url, callback=self.get_pages)

    def get_pages(self, response):
        result = response.json()
        total_count = int(result["d"]["__count"])
        offset = 0

        while offset < total_count:
            yield scrapy.Request(self.base_url + f"&$skip={offset}")
            offset += 250

    def parse(self, response):
        result = response.json()

        for station in result["d"]["results"]:
            yield GeojsonPointItem(
                lat=station["Latitude"],
                lon=station["Longitude"],
                name=station["Name"],
                addr_full=station["AddressLine"],
                city=station["Locality"],
                state=station["AdminDistrict"],
                postcode=station["PostalCode"],
                country=station["CountryRegion"],
                phone=station["Phone"],
                ref=station["EntityID"],
                brand=BRANDS[station["Brand"]],
                brand_wikidata=WIKIBRANDS[station["Brand"]],
                opening_hours="24/7" if station["TFH"] else "",
                extras={
                    "amenity:fuel": True,
                    "fuel:e85": station["e85"],
                    "fuel:diesel": station["Diesel"],
                    "fuel:biodiesel": station["rd"],
                    "car_wash": station["CarWash"],
                    "shop": "convenience"
                    if station["CStore"]
                    else "kiosk"
                    if station["Snacks"]
                    else None,
                    "atm": station["ATM"],
                },
            )
