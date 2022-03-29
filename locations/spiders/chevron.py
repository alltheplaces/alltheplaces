# -*- coding: utf-8 -*-
import scrapy
import urllib

from locations.items import GeojsonPointItem

HEADERS = {"Content-Type": "application/json"}

WIKIBRANDS = {"Chevron": "Q319642", "Texaco": "Q775060"}


class ChevronSpider(scrapy.Spider):
    name = "chevron"
    item_attributes = {"brand": "Chevron", "brand_wikidata": "Q319642"}
    allowed_domains = ["www.chevronwithtechron.com"]
    download_delay = 0.2

    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_10mile_radius.csv"
        ) as points:
            next(points)  # skip the header row
            for point in points:
                row = point.split(",")

                yield scrapy.FormRequest(
                    url="https://www.chevronwithtechron.com/webservices/ws_getChevronTexacoNearMe_r2.aspx",
                    method="GET",
                    formdata={
                        "brand": "chevronTexaco",
                        "radius": "10",
                        "lat": row[1].strip(),
                        "lng": row[2].strip(),
                    },
                )

    def parse(self, response):
        result = response.json()

        if int(result["count"]) == 50:
            self.logger.warning(
                "received maximum number of stations, reduce the search radius to make sure we don't miss any"
            )

        for station in result["stations"]:
            yield GeojsonPointItem(
                lat=station["lat"],
                lon=station["lng"],
                name=station["name"],
                addr_full=station["address"],
                city=station["city"],
                state=station["state"],
                postcode=station["zip"],
                country="US",
                phone=station["phone"],
                website=f"https://www.chevronwithtechron.com/station/id{station['id']}",
                opening_hours=station["hours"],
                ref=station["id"],
                brand=station["brand"],
                brand_wikidata=WIKIBRANDS[station["brand"]],
                extras={
                    "amenity:fuel": True,
                    "amenity:toilets": station["restroom"] == "1",
                    "car_wash": station["carwash"] == "1",
                    "fuel:diesel": station["diesel"] == "1",
                    "hgv": station["truckstop"] == "1",
                    "shop": "convenience" if station["cstore"] == "1" else None,
                },
            )
