# -*- coding: utf-8 -*-
import re
import scrapy
import urllib.parse

from locations.items import GeojsonPointItem


class BassProSpider(scrapy.Spider):
    name = "bassproshops"
    item_attributes = {"brand": "Bass Pro Shops", "brand_wikidata": "Q4867953"}
    allowed_domains = ["stores.basspro.com"]
    start_urls = ("https://stores.basspro.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            path = urllib.parse.urlparse(url).path
            if path.count("/") != 4:
                continue
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        main = response.xpath('//div[@id="hero"]/..')

        store_id_js_text = str(
            response.xpath("//script/text()")[3].extract()
        )  # store id from JS var filter
        store_id = re.search(r"(?<=storeid: )\d*", store_id_js_text).group()

        properties = {
            "name": main.xpath('.//h1[@itemprop="name"]/span/text()').get(),
            "lat": main.xpath('.//*[@itemprop="latitude"]/@content').get(),
            "lon": main.xpath('.//*[@itemprop="longitude"]/@content').get(),
            "ref": store_id,
            "website": response.url,
            "addr_full": main.xpath('.//*[@itemprop="streetAddress"]/span/text()')
            .get()
            .strip(),
            "city": main.xpath('.//*[@itemprop="addressLocality"]/text()').get(),
            "state": main.xpath('.//*[@itemprop="addressRegion"]/text()').get(),
            "postcode": main.xpath('.//*[@itemprop="postalCode"]/text()').get().strip(),
            "country": main.xpath('.//*[@itemprop="addressCountry"]/text()').get(),
            "phone": main.xpath('.//*[@itemprop="telephone"]/text()').get(),
            "opening_hours": "; ".join(
                main.xpath('.//*[@itemprop="openingHours"]/@content').extract()
            ),
        }

        yield GeojsonPointItem(**properties)
