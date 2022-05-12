# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AldiDESpider(scrapy.Spider):
    name = "aldi_de"
    item_attributes = {"brand": "Aldi", "brand_wikidata": "Q41171373"}
    allowed_domains = ["www.yellowmap.de"]
    start_urls = (
        "https://www.yellowmap.de/Presentation/AldiSued/de-DE/ResultList?LocX=&LocY=&HiddenBranchCode=&BranchCode=&Lux=-14.150390625&Luy=73.9710776393399&Rlx=38.408203125&Rly=49.95121990866204&ZoomLevel=4&Mode=None&Filters.OPEN=false&Filters.ASxFITF=false&Filters.ASxFIPA=false&Filters.ASxFIBA=false&Filters.ASxFIEL=false&Filters.ASxNEDE=false&Filters.ASxKAFE=false&Filters.ASxKUWI=false&Filters.ASxBACK=false&Filters.ASxFIGS=false&_=1586528054615",
    )

    def parse(self, response):
        data = response.json()
        container = data["Container"]
        stores = self.parse_data(container)

        for store in stores:
            json_data = json.loads(
                store.css(".resultItem::attr(data-json)").extract_first()
            )
            ref = json_data["id"]
            lat = json_data["locY"]
            lon = json_data["locX"]
            name = store.css(".resultItem-CompanyName::text").extract_first()
            street = store.css(".resultItem-Street::text").extract_first()
            address1 = store.css(".resultItem-City::text").extract_first().split(",")[0]

            (zipcode, city) = re.search(r"(\d+)(.*)", address1).groups()

            properties = {
                "ref": ref,
                "name": name,
                "lat": lat,
                "lon": lon,
                "addr_full": street.strip(),
                "city": city.strip(),
                "postcode": zipcode.strip(),
            }

            yield GeojsonPointItem(**properties)

        with open(
            "./locations/searchable_points/eu_centroids_20km_radius_country.csv"
        ) as points:
            next(points)  # Ignore the header
            for point in points:
                _, lat, lon, country = point.strip().split(",")
                if country == "DE":
                    yield scrapy.Request(
                        "https://www.yellowmap.de/Presentation/AldiSued/de-DE/ResultList?LocX={}&LocY={}&ZoomLevel={}".format(
                            lon, lat, 8
                        ),
                        callback=self.parse,
                    )

    def parse_data(self, data):
        data = scrapy.http.HtmlResponse(url="", body=data, encoding="utf-8")
        stores = data.css(".resultItem")
        if stores:
            return stores
        else:
            return []
