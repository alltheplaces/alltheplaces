# -*- coding: utf-8 -*-
import re
import scrapy

from locations.items import GeojsonPointItem


class SinclairSpider(scrapy.Spider):
    name = "sinclair"
    item_attributes = {"brand": "Sinclair", "brand_wikidata": "Q1290900"}
    allowed_domains = ["www.sinclairoil.com"]

    def start_requests(self):
        yield scrapy.Request(
            "https://www.sinclairoil.com/location-feed", callback=self.add_locations
        )

    def add_locations(self, response):
        yield scrapy.Request(
            "https://www.sinclairoil.com/truck-stop-feed",
            callback=self.add_truck_stops,
            meta={"locations": self.parse_location_feed(response, "general")},
        )

    def add_truck_stops(self, response):
        yield scrapy.Request(
            "https://www.sinclairoil.com/gold-truck-stop-feed",
            callback=self.add_gold_truck_stops,
            meta={
                "locations": response.meta["locations"]
                + self.parse_location_feed(response, "truck_stop")
            },
        )

    def add_gold_truck_stops(self, response):
        yield scrapy.Request(
            "https://www.sinclairoil.com/customers/location-list?page=0",
            meta={
                "locations": response.meta["locations"]
                + self.parse_location_feed(response, "truck_stop")
            },
        )

    def parse_location_feed(self, feed_response, type):
        feed_response.selector.remove_namespaces()
        locations = []

        for pm in feed_response.xpath("//Placemark"):
            coordinates = pm.xpath("Point/coordinates/text()").get()
            (lon, lat, _) = coordinates.split(",")

            locations.append(
                {
                    "type": type,
                    "name": pm.xpath("name/text()").get().strip(),
                    "description": pm.xpath("description/text()").get().strip(),
                    "lon": lon,
                    "lat": lat,
                }
            )

        return locations

    def parse(self, response):
        locations = response.meta["locations"]

        for row in response.css(".views-table tbody tr"):
            name = row.css(".views-field-title::text").get().strip()
            address = row.css(".views-field-field-physical-address::text").get().strip()
            city = row.css(".views-field-field-city::text").get().strip()
            state = row.css(".views-field-field-state::text").get().strip()
            postcode = row.css(".views-field-field-zip-code::text").get().strip()
            phone = row.css(".views-field-field-phone-number::text").get().strip()

            self.logger.info(address)
            self.logger.info(postcode)

            lat = None
            lon = None
            truck_stop = None

            try:
                location = next(
                    l
                    for l in locations
                    if (address in l["description"] and postcode in l["description"])
                )

                truck_stop = location["type"] == "truck_stop"
                lon = location["lon"]
                lat = location["lat"]
            except StopIteration:
                map_url = row.xpath(".//a/@href").get()
                match = re.search(r"@(.+),(.+),.+z$", map_url)
                if match:
                    (lat, lon) = match.groups()
                else:
                    continue

            yield GeojsonPointItem(
                lon=lon,
                lat=lat,
                ref=phone,
                name=name,
                addr_full=address,
                city=city,
                state=state,
                postcode=postcode,
                country="US",
                phone=phone,
                extras={
                    "amenity:fuel": True,
                    "hgv": truck_stop,
                    "fuel:diesel": truck_stop or None,
                },
            )

        last_page_url = response.css(".pager-last a::attr(href)").get()

        if last_page_url:
            current_page = int(response.url.split("page=")[-1])

            yield scrapy.Request(
                f"https://www.sinclairoil.com/customers/location-list?page={current_page + 1}",
                meta=response.meta,
            )
