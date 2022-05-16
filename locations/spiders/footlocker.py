# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

OPEN_STREET_MAP_OPENING_HOURS_SINGLE_DAY_REGEX = r"([a-zA-Z,]+)\s([\d:]+)-([\d:]+)"
STORES_REGEX = r"https://stores.footlocker.com/.+/.+/.+/.+.html"


class FootLockerSpider(scrapy.Spider):
    name = "footlocker"
    item_attributes = {"brand": "Foot Locker", "brand_wikidata": "Q63335"}
    allowed_domains = ["stores.footlocker.com"]
    start_urls = ("https://stores.footlocker.com/sitemap.xml",)

    def find_store_urls(self, urls: list) -> list:
        store_urls = []
        for url in urls:
            if re.match(STORES_REGEX, url):
                store_urls.append(url)
        return store_urls

    def parse_hours(self, hours: list) -> OpeningHours:
        opening_hours = OpeningHours()
        for group in hours:
            try:
                day, open_time, close_time = re.search(
                    OPEN_STREET_MAP_OPENING_HOURS_SINGLE_DAY_REGEX, group
                ).groups()
                opening_hours.add_range(day, open_time, close_time)
            except AttributeError:
                continue

        return opening_hours

    def parse_store(self, response):
        # The @itemid points to a url with a #numeric_store_id, but the url just redirects to store.footlocker.com.
        # But we can still use the #numeric_store_id in the url for ref.
        ref = (
            response.xpath('//*[@itemtype="http://schema.org/ShoeStore"]/@itemid')
            .extract_first()
            .split("#")[1]
        )

        # The name can be split across multiple child elements so we need to join them together here.
        name = "".join(
            response.xpath(
                '//*[@itemprop="name"][@id="location-name"]//text()'
            ).extract()
        )
        phone = response.xpath('//*[@itemprop="telephone"]/text()').extract_first()
        website = response.url

        # Foot Locker provides address data via http://schema.org/PostalAddress microdata.
        addr_full = response.xpath(
            '//meta[@itemprop="streetAddress"]/@content'
        ).extract_first()
        city = response.xpath(
            '//meta[@itemprop="addressLocality"]/@content'
        ).extract_first()
        state = response.xpath('//*[@itemprop="addressRegion"]//text()').extract_first()
        postcode = response.xpath('//*[@itemprop="postalCode"]/text()').extract_first()
        country = response.xpath(
            '//*[@itemprop="addressCountry"]/text()'
        ).extract_first()

        # Foot Locker provides lat/lon via http://schema.org/GeoCoordinates microdata.
        lat = float(
            response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
        )
        lon = float(
            response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
        )

        properties = {
            "ref": ref,
            "name": name,
            "addr_full": addr_full,
            "city": city,
            "state": state,
            "postcode": postcode,
            "country": country,
            "phone": phone,
            "website": website,
            "lat": lat,
            "lon": lon,
        }

        # Hours are listed in OpenStreetMap's opening_hours format but per day, so we need to convert the list of hours
        # into a single string using the OpeningHours object.
        hours = response.xpath('//*[@itemprop="openingHours"]/@content').extract()
        parsed_hours = self.parse_hours(hours)
        if parsed_hours.as_opening_hours():
            properties["opening_hours"] = parsed_hours.as_opening_hours()

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        # Footlocker provides a sitemap.xml that includes URLs for subdirectories and URLs for stores.
        # Extract only the store URLs from the site map.
        response.selector.remove_namespaces()
        urls = response.xpath("/urlset/url/loc/text()").extract()
        store_urls = self.find_store_urls(urls)

        for url in store_urls:
            yield scrapy.Request(url, callback=self.parse_store)
