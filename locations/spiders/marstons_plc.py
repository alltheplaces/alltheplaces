# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class MarstonsPlcSpider(scrapy.Spider):
    name = "marstons_plc"
    item_attributes = {"brand": "Marston's", "brand_wikidata": "Q6773982"}
    allowed_domains = ["marstons.co.uk"]

    def start_requests(self):
        url = "https://www.marstons.co.uk/ajax/finder/markers/"

        headers = {
            "origin": "https://www.marstons.co.uk",
            "Referer": "https://www.marstons.co.uk/pubs/finder/",
            "content-type": "application/json; charset=utf-8",
        }

        current_state = json.dumps({"s": 1, "pp": 48})

        yield scrapy.Request(
            url,
            method="POST",
            body=current_state,
            headers=headers,
            callback=self.parse_store_ids,
        )

    def parse_store_ids(self, response):
        store_ids = response.json()
        ids = []

        for id in store_ids["markers"]:
            ids.append(id["i"])

        count = 1
        params = ""

        ## Adding all the ids together makes the url too large
        for i in ids:
            if count < 47:
                params = params + "p=" + str(i)
                params = params + "&"
            else:
                url = "https://www.marstons.co.uk/ajax/finder/outlet/?"
                params = params[:-1]
                url = url + params
                count = 0
                params = ""
                yield scrapy.Request(url, callback=self.parse)

            count += 1

        url = "https://www.marstons.co.uk/ajax/finder/outlet/?"
        params = params[:-1]
        url = url + params
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        data = response.json()
        places = data["outlets"]

        for place in places:
            address = place["address"]
            city = place["town"].split(",")
            addr = address.split(", ")
            if len(addr) == 4:
                str_addr = addr[0]
                state = addr[2]
                postal = addr[3]
            elif len(addr) == 3:
                str_addr = addr[0]
                state = ""
                postal = addr[2]
            elif len(addr) == 5:
                str_addr = addr[0]
                state = addr[3]
                postal = addr[4]
            elif len(addr) == 6:
                str_addr = addr[0]
                state = addr[4]
                postal = addr[5]

            properties = {
                "ref": place["phc"],
                "name": place["name"],
                "addr_full": str_addr,
                "city": city[0],
                "state": state,
                "postcode": postal,
                "country": "GB",
                "lat": place["lat"],
                "lon": place["lng"],
                "phone": place["tel"],
                "website": place["url"],
            }

            yield GeojsonPointItem(**properties)
