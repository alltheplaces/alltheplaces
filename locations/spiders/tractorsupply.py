# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class TractorSupplySpider(SitemapSpider):
    name = "tractorsupply"
    item_attributes = {"brand": "Tractor Supply", "brand_wikidata": "Q15109925"}
    allowed_domains = ["tractorsupply.com"]
    sitemap_urls = ["https://www.tractorsupply.com/sitemap_stores.xml"]
    sitemap_rules = [
        (
            "https:\/\/www\.tractorsupply\.com\/tsc\/([\w\-_]+)$",
            "parse",
        ),
    ]
    download_delay = 1.5
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (X11; CrOS aarch64 14324.72.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.91 Safari/537.36",
    }
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": headers,
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"
        },
    }

    def parse_hours(self, hours):
        day_hour = hours.split("|")

        opening_hours = OpeningHours()

        for dh in day_hour:
            try:
                day = dh.split("=")[0][:2]
                hr = dh.split("=")[1]
                open_time, close_time = hr.split("-")
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M %p",
                )
            except:
                continue

        return opening_hours.as_opening_hours()

    def parse(self, response):
        store = response.xpath('//*[@itemtype="http://schema.org/Store"]')

        address = store.xpath("//*/address")
        geocoordinates = address.xpath(
            '//*[@itemtype="http://schema.org/GeoCoordinates"]'
        )
        postaladdress = address.xpath(
            '//*[@itemtype="http://schema.org/PostalAddress"]'
        )

        properties = {
            "ref": response.xpath('//*[@id="physicalStoreId"]/@value').get(),
            "name": store.xpath('.//*[@itemprop="name"]/text()').get().strip(),
            "addr_full": postaladdress.xpath(
                '//*[@itemprop="streetAddress"]/text()'
            ).get(),
            "city": postaladdress.xpath(
                '//*[@itemprop="addressLocality"]/text()'
            ).get(),
            "state": postaladdress.xpath('//*[@itemprop="addressRegion"]/text()').get(),
            "postcode": postaladdress.xpath('//*[@itemprop="postalCode"]/text()').get(),
            "country": postaladdress.xpath(
                '//*[@itemprop="addressCountry"]/text()'
            ).get(),
            "lon": float(
                geocoordinates.xpath('//*/meta[@itemprop="longitude"]/@content').get()
            ),
            "lat": float(
                geocoordinates.xpath('//*/meta[@itemprop="latitude"]/@content').get()
            ),
            "phone": response.xpath('//*[@itemprop="Telephone"]/text()').get().strip(),
            "website": response.url,
        }

        opening_hours = self.parse_hours(
            response.xpath('//*[@id="storeHour0"]/@value').get()
        )
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)
