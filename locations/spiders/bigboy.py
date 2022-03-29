# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class WalmartSpider(scrapy.Spider):
    name = "bigboy"
    item_attributes = {"brand": "Big Boy"}
    allowed_domains = ["www.bigboy.com"]
    start_urls = ("http://www.bigboy.com/locations",)

    def parse(self, response):
        stores = response.xpath('//div[@id="locations"]/div')

        for store in stores:
            url = store.xpath("@itemtype")[0].extract()
            name = store.xpath(
                'div[@class="thumbnail"]/strong[@itemprop="name"]/text()'
            )[0].extract()
            street = store.xpath(
                'div[@class="thumbnail"]/div[@itemprop="address"]/span[@itemprop="streetAddress"]/text()'
            )[0].extract()
            locality = store.xpath(
                'div[@class="thumbnail"]/div[@itemprop="address"]/span[@itemprop="addressLocality"]/text()'
            )[0].extract()
            region = store.xpath(
                'div[@class="thumbnail"]/div[@itemprop="address"]/span[@itemprop="addressRegion"]/text()'
            )[0].extract()
            postalcode = store.xpath(
                'div[@class="thumbnail"]/div[@itemprop="address"]/span[@itemprop="postalCode"]/text()'
            )[0].extract()
            phone = store.xpath(
                'div[@class="thumbnail"]/div[@itemprop="address"]/span[@itemprop="telephone"]/text()'
            )[0].extract()
            lat = store.xpath(
                'div[@class="thumbnail"]/div[@itemprop="geo"]/meta[@itemprop="latitude"]/@content'
            )[0].extract()
            lon = store.xpath(
                'div[@class="thumbnail"]/div[@itemprop="geo"]/meta[@itemprop="longitude"]/@content'
            )[0].extract()

            yield GeojsonPointItem(
                lat=lat,
                lon=lon,
                ref=name,
                phone=phone,
                name=name,
                opening_hours="",
                addr_full=street,
                city=locality,
                state=region,
                postcode=postalcode,
                website=url,
            )
