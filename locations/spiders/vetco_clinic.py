# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from scrapy.selector import Selector


class VetcoSpider(scrapy.Spider):
    name = "vetco"
    item_attributes = {"brand": "vetcoclinics"}
    allowed_domains = ["vetcoclinics.com"]
    start_urls = (
        "https://www.vetcoclinics.com/services-and-clinics/vaccination-clinics-by-state/",
    )

    def start_requests(self):
        with open("./locations/searchable_points/us_zcta.csv") as points:
            next(points)  # Ignore the header
            for point in points:
                row = point.split(",")
                zip = row[0].strip().strip('"')

                url = f"https://www.vetcoclinics.com/_assets/dynamic/ajax/locator.php?zip={zip}"

                yield scrapy.http.Request(url, self.parse, method="GET")

    def parse(self, response):
        jsonresponse = response.json()
        if jsonresponse is not None:
            clinics = jsonresponse.get("clinics")
            if clinics:
                for stores in clinics:
                    body = stores["label"]
                    address = Selector(text=body).xpath("//address/text()").extract()
                    if len(address) == 3:
                        addr_full, city_state_postal, phone = [
                            item.split(",") for item in address
                        ]
                        city, state_postal = [
                            item.split(",") for item in city_state_postal
                        ]
                        state, postal = re.search(
                            r"([A-Z]{2}) (\d{5})", state_postal[0]
                        ).groups()

                    else:
                        addr_full, city_state_postal = [
                            item.split(",") for item in address
                        ]
                        city, state_postal = [
                            item.split(",") for item in city_state_postal
                        ]
                        state, postal = re.search(
                            r"([A-Z]{2}) (\d{5})", state_postal[0]
                        ).groups()

                    properties = {
                        "ref": addr_full[0].strip(),
                        "addr_full": addr_full[0].strip(),
                        "city": city[0].strip(),
                        "state": state,
                        "postcode": postal,
                        "lat": float(stores["point"]["lat"]),
                        "lon": float(stores["point"]["long"]),
                        "website": response.url,
                    }

                    yield GeojsonPointItem(**properties)
