# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

from locations.hours import OpeningHours


class GeojsonPointItem(scrapy.Item):
    lat = scrapy.Field()
    lon = scrapy.Field()
    name = scrapy.Field()
    addr_full = scrapy.Field()
    housenumber = scrapy.Field()
    street = scrapy.Field()
    street_address = scrapy.Field()
    city = scrapy.Field()
    state = scrapy.Field()
    postcode = scrapy.Field()
    country = scrapy.Field()
    phone = scrapy.Field()
    website = scrapy.Field()
    twitter = scrapy.Field()
    facebook = scrapy.Field()
    opening_hours = scrapy.Field()
    image = scrapy.Field()
    ref = scrapy.Field()
    brand = scrapy.Field()
    brand_wikidata = scrapy.Field()
    located_in = scrapy.Field()
    located_in_wikidata = scrapy.Field()
    extras = scrapy.Field()

    def from_linked_data(self, ld):
        if ld.get("geo"):
            if ld["geo"].get("@type") == "GeoCoordinates":
                self["lat"] = ld["geo"].get("latitude")
                self["lon"] = ld["geo"].get("longitude")

        self["name"] = ld.get("name")

        if ld.get("address"):
            if isinstance(ld["address"], str):
                self["addr_full"] = ld["address"]
            elif ld["address"].get("@type") == "PostalAddress":
                self["street_address"] = ld["address"].get("streetAddress")
                self["city"] = ld["address"].get("addressLocality")
                self["state"] = ld["address"].get("addressRegion")
                self["postcode"] = ld["address"].get("postalCode")
                self["country"] = ld["address"].get("addressCountry")

        self["phone"] = ld.get("telephone")
        self["website"] = ld.get("url")

        oh = OpeningHours()
        oh.from_linked_data(ld)
        self["opening_hours"] = oh.as_opening_hours()

        if ld.get("image"):
            if isinstance(ld["image"], str):
                self["image"] = ld["image"]
            elif ld["image"].get("@type") == "ImageObject":
                self["image"] = ld["image"].get("contentUrl")

        self["ref"] = ld.get("branchCode")

        if ld.get("brand"):
            if isinstance(ld["brand"], str):
                self["brand"] = ld["brand"]
            elif (
                ld["brand"].get("@type") == "Brand"
                or ld["brand"].get("@type") == "Organization"
            ):
                self["brand"] = ld["brand"].get("name")
