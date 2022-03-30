# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from scrapy.selector import Selector


class CalvinKleinSpider(scrapy.Spider):
    name = "calvin_klein"
    item_attributes = {"brand": "Calvin Klein"}
    allowed_domains = ["gotwww.com", "calvinklein.com"]

    def start_requests(self):
        states = [
            "Alabama",
            "Arizona",
            "California",
            "Colorado",
            "Connecticut",
            "Delaware",
            "Florida",
            "Georgia",
            "Hawaii",
            "Illinois",
            "Indiana",
            "Kentucky",
            "Louisiana",
            "Maine",
            "Maryland",
            "Massachusetts",
            "Michigan",
            "Minnesota",
            "Mississippi",
            "Missouri",
            "Montana",
            "Nevada",
            "New Hampshire",
            "New Jersey",
            "New York",
            "Ohio",
            "Oregon",
            "Pennsylvania",
            "South Carolina",
            "Tennessee",
            "Texas",
            "Utah",
            "Virginia",
            "Washington",
            "Wisconsin",
            "Alberta",
            "British Columbia",
            "Manitoba",
            "Ontario",
            "Quebec",
        ]

        s_url = (
            "https://secure.gotwww.com/gotlocations.com/ck.com/ckna.php?address={state}"
        )

        for state in states:
            url = s_url.format(state=state)
            yield scrapy.Request(url=url, callback=self.parse_us_ca)

        ## UK, FR/LU, DE, BE/NL, ES, TR, RS, XK, AM, BY, GE, UH, LB, EG, IL, JO, RU, ZA
        ## Europe and MEA+
        europe = [
            "715837896",
            "715837898",
            "715837895",
            "715837892",
            "715837887",
            "715837894",
            "715837933",
            "715837936",
            "715837922",
            "715837917",
            "715837938",
            "715837908",
            "715837888",
            "715837900",
            "715837930",
            "715837912",
            "715837886",
            "715837934",
        ]

        e_url = "https://www.calvinklein.co.uk/wcs/resources/store/20027/storelocator/byGeoNode/{code}"
        for code in europe:
            url = e_url.format(code=code)
            yield scrapy.Request(url=url, callback=self.parse_europe)

        ## Australia
        yield scrapy.Request(
            url="https://www.calvinklein.com.au/stores/index/dataAjax/?_=1573849948857",
            callback=self.parse_au,
        )

    def parse_au(self, response):
        data = response.json()

        for store in data:
            properties = {
                "ref": store["i"],
                "name": "Calvin Klein",
                "addr_full": store["a"][0],
                "city": store["a"][1],
                "state": store["a"][2],
                "postcode": store["a"][3],
                "country": "Australia",
                "lat": store["l"],
                "lon": store["g"],
                "phone": store["p"],
            }

            yield GeojsonPointItem(**properties)

    def parse_europe(self, response):
        data = response.json()

        for store in data["PhysicalStore"]:
            try:
                state = store["stateOrProvinceName"]
            except:
                state = "Europe"
            try:
                postal = store["postalCode"].strip()
            except:
                postal = ""

            properties = {
                "ref": store["storeName"],
                "name": "Calvin Klein",
                "addr_full": store["addressLine"][0],
                "city": store["city"],
                "state": state,
                "postcode": postal,
                "country": store["country"],
                "lat": store["latitude"],
                "lon": store["longitude"],
            }

            yield GeojsonPointItem(**properties)

    def parse_us_ca(self, response):
        data = response.xpath('//script[contains(.,"map")]/text()').extract_first()
        places = re.findall("L.marker(.*)", data)

        for place in places:
            coordinates = re.search(r"\[(.*)\]", place).groups()[0]
            coords = coordinates.split(",")

            html = re.search(r"bindPopup\('(.*)'\);", place).groups()[0]

            info = (
                Selector(text=html)
                .xpath('//*[@class="map_text"]/table/tr[7]/td/text()')
                .getall()
            )
            if len(info) == 5:
                country = info[3]
                phone = info[4]
                city = re.search(r"^(.*),", info[2]).groups()[0]
                state = re.search(r",\s([A-Z]{2})", info[2]).groups()[0]
                postal = re.search(r"[A-Z]{2}\s(.*)", info[2]).groups()[0]
            elif len(info) == 4:
                country = info[2]
                phone = info[3]
                city = re.search(r"^(.*),", info[1]).groups()[0]
                state = re.search(r",\s([A-Z]{2})", info[1]).groups()[0]
                postal = re.search(r"[A-Z]{2}\s(.*)", info[1]).groups()[0]

            ## Other countries show up in some searches
            if country not in ["United States", "Canada"]:
                pass
            else:
                properties = {
                    "ref": info[0],
                    "name": "Calvin Klein",
                    "addr_full": info[0],
                    "city": city,
                    "state": state,
                    "postcode": postal,
                    "country": country,
                    "lat": coords[0],
                    "lon": coords[1],
                    "phone": phone,
                }

                yield GeojsonPointItem(**properties)
