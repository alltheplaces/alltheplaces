import re

import scrapy

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature


class MediaMarktBESpider(scrapy.Spider):
    name = "media_markt_be"
    item_attributes = {"brand": "MediaMarkt", "brand_wikidata": "Q2381223"}
    start_urls = ["https://www.mediamarkt.be/fr/marketselection.html"]
    domain = "https://www.mediamarkt.be"

    def parse(self, response):
        store_urls = response.css(".all-markets-list").xpath("./li/a/@href").extract()
        for store_url in store_urls:
            yield scrapy.http.Request(
                url=self.domain + store_url,
                method="GET",
                callback=self.parse_store,
            )

    def parse_store(self, response):
        store = response.xpath('//*[@itemtype="https://schema.org/LocalBusiness"]')
        address = store.xpath("//*/address")
        postaladdress = address.xpath('//*[@itemtype="https://schema.org/PostalAddress"]')
        geocoordinates = address.xpath('//*[@itemtype="https://schema.org/GeoCoordinates"]')

        ref = response.url
        name = store.xpath('//*[@id="my-market-content"]/h1/text()').get()
        street_address = postaladdress.xpath('//*[@itemprop="streetAddress"]/text()').get()
        street = street_address.rsplit(" ", 1)[0]
        housenumber = street_address.rsplit(" ", 1)[1]
        city = postaladdress.xpath('//*[@itemprop="addressLocality"]/text()').get()
        postcode = postaladdress.xpath('//*[@itemprop="postalCode"]/text()').get().strip()
        addr_full = street_address + ", " + postcode + " " + city
        lon = float(geocoordinates.xpath('//*/meta[@itemprop="longitude"]/@content').get())
        lat = float(geocoordinates.xpath('//*/meta[@itemprop="latitude"]/@content').get())
        phone = postaladdress.xpath('//*[@itemprop="telephone"]/text()').get()
        website = response.url
        email = postaladdress.xpath('//*[@itemprop="email"]/text()').get()

        properties = {
            "ref": ref,
            "name": name,
            "addr_full": addr_full,
            "street_address": street_address,
            "housenumber": housenumber,
            "street": street,
            "city": city,
            "postcode": postcode,
            "lon": lon,
            "lat": lat,
            "phone": phone,
            "website": website,
            "email": email,
        }

        opening_hours = self.parse_hours(response)
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield Feature(**properties)

    def parse_hours(self, response):
        opening_hours = OpeningHours()

        store = response.xpath('//*[@itemtype="https://schema.org/LocalBusiness"]')
        if store:
            all_hours = store.xpath('//*[@itemprop="openingHours"]/@content')
            regex = re.compile(r"(lu|ma|me|je|ve|sa|su)\s+(\d{2}:\d{2})\s*-(\d{2}:\d{2})")
            for hours in all_hours:
                hours_str = hours.get().strip()
                match = re.search(regex, hours_str)
                if match:
                    day_of_week = match.group(1).capitalize()
                    open_time = match.group(2)
                    close_time = match.group(3)

                    if close_time == "00:00":
                        close_time = "23:59"

                    opening_hours.add_range(day=DAYS_FR[day_of_week], open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()
