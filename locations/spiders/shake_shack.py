# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class ShakeShackSpider(scrapy.Spider):
    name = "shake_shack"
    item_attributes = {"brand": "Shake Shack"}
    allowed_domains = ["www.shakeshack.com"]
    start_urls = ("https://www.shakeshack.com/locations/",)

    def parse(self, response):
        locations = response.xpath('//a[contains(@href, "location/")]')

        for location in locations:
            location_url = location.xpath("@href").extract()[0]
            full_url = response.urljoin(location_url)
            yield scrapy.Request(
                full_url,
                callback=self.parse_location,
            )

    def parse_location(self, response):
        cityState = response.xpath('//h1[@class="sr-only"]/text()').extract_first()
        city = cityState.split(",")[-2]
        state = cityState.split(",")[-1]
        phone = (
            response.xpath('//div[@class="span4 address"]/p/text()')
            .extract()[-1]
            .strip()
        )
        fullAddress = response.xpath(
            '//div[@id="map-infowindow"]/p/text()'
        ).extract_first()
        fullAddressArray = fullAddress.split(",")
        postcode = fullAddressArray[-1].split(" ")[-1].strip()

        yield GeojsonPointItem(
            name=cityState,
            ref=cityState,
            addr_full=fullAddress,
            city=city,
            state=state,
            postcode=postcode,
            phone=phone,
        )
