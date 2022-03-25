# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class LandsEndSpider(scrapy.Spider):
    name = "landsend"
    item_attributes = {"brand": "Lands' End"}
    allowed_domains = ["landsend.com"]

    def start_requests(self):
        base_url = "https://www.landsend.com/pp/StoreLocator?lat={lat}&lng={lng}&radius=100&S=S&L=L&C=undefined&N=N"
        with open(
            "./locations/searchable_points/us_centroids_100mile_radius.csv"
        ) as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        for store in response.xpath("//markers/marker"):
            if store:
                properties = {
                    "ref": store.xpath("./@storenumber").extract_first(),
                    "name": store.xpath("./@name").extract_first(),
                    "addr_full": store.xpath("./@address").extract_first(),
                    "city": store.xpath("./@city").extract_first(),
                    "state": store.xpath("./@state").extract_first(),
                    "postcode": store.xpath("./@zip").extract_first(),
                    "phone": store.xpath("./@phonenumber").extract_first(),
                    "lat": float(store.xpath("./@lat").extract_first()),
                    "lon": float(store.xpath("./@lng").extract_first()),
                    "website": response.url,
                }

                yield GeojsonPointItem(**properties)
