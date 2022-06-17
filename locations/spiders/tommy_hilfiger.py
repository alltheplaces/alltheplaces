# -*- coding: utf-8 -*-
import json
import scrapy

from locations.items import GeojsonPointItem


class TommyHilfigerSpider(scrapy.Spider):
    name = "tommy_hilfiger"
    item_attributes = {"brand": "Tommy Hilfiger", "brand_wikidata": "Q634881"}
    allowed_domains = ["tommy.com"]
    start_urls = [
        "https://uk.tommy.com/wcs/resources/store/30027/geonode?q=byGeoNodeTypeAndName&type=CNTY&name=&siteLevelSearch=true"
    ]

    def parse(self, response):
        regions = response.json()["GeoNode"]
        for region in regions:
            yield scrapy.Request(
                "https://uk.tommy.com/wcs/resources/store/30027/storelocator/byGeoNode/"
                + region["uniqueID"],
                callback=self.parse_stores,
            )

    def parse_stores(self, response):
        stores = response.json()
        if not stores.get("PhysicalStore"):
            return

        stores = stores["PhysicalStore"]

        for store in stores:
            properties = {
                "ref": store["storeName"],
                "name": store["Description"][0]["displayStoreName"],
                "street_address": store["addressLine"][0],
                "city": store["city"],
                "country": store["country"],
                "lat": store["latitude"],
                "lon": store["longitude"],
            }
            if store.get("postalCode"):
                properties["postcode"] = store["postalCode"].strip()
            if store.get("telephone1"):
                properties["phone"] = store["telephone1"].strip()

            yield GeojsonPointItem(**properties)
