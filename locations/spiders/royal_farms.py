# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Royal_farmsSpider(scrapy.Spider):
    name = "royal_farms"
    item_attributes = {"brand": "Royal Farms", "brand_wikidata": "Q7374169"}
    allowed_domains = ["royalfarms.com"]
    start_urls = [
        "https://www.royalfarms.com/location_results.asp",
    ]

    def parse(self, response):
        states = response.xpath('//select[@id="state"]/option/@value').extract()

        url = "https://www.royalfarms.com/location_results.asp"

        for state in states:
            if state and state != "":
                form_data = {"submitStore": "yes", "state": state}

                yield scrapy.http.FormRequest(
                    url=url,
                    method="POST",
                    formdata=form_data,
                    callback=self.parse_stores,
                )

    def parse_stores(self, response):
        rows = response.xpath('//tr[@class="listdata"]')

        for row in rows:
            store = row.xpath('./td[@class="listdata"][1]')
            hours = row.xpath('./td[@class="listdata"][2]/em/text()').get()
            amenities = row.xpath('./td[@class="listdata"][3]/img/@src').getall()

            store_number = store.xpath("./strong/text()").re_first(r"STORE #(\d+)")
            self.logger.warn(store_number)
            addr_parts = store.xpath("./text()").extract()
            addr_parts = list(
                filter(None, [x.replace("\xa0", " ").strip() for x in addr_parts])
            )
            phone = addr_parts.pop(-1)
            last_line = addr_parts.pop(-1)
            city, state, postal = re.search(
                r"(.+?), ([A-Z]{2}) (\d{5})", last_line
            ).groups()
            address = " ".join(addr_parts)

            properties = {
                "ref": store_number,
                "addr_full": address,
                "city": city,
                "state": state,
                "postcode": postal,
                "country": "US",
                "phone": phone,
                "opening_hours": "24/7" if hours and "24 Hours" in hours else None,
                "extras": {
                    "amenity:chargingstation": "uploads/icon_electricveh_charging.png"
                    in amenities,
                    "amenity:fuel": "uploads/icon_gas.png" in amenities,
                    # This icon actually means that there's DEF in the fuel lanes,
                    # which is a good indicator that it also has diesel fuel.
                    # There's no direct icon for diesel fuel availability though,
                    # and I've some stations that have diesel don't have DEF.
                    "fuel:diesel": "uploads/icon_diesel.png" in amenities or None,
                    "fuel:e15": "uploads/icon_ethanol15percent.png" in amenities
                    or None,
                    "fuel:e85": "uploads/icon_gas_flexfuel.png" in amenities or None,
                },
            }

            yield GeojsonPointItem(**properties)
