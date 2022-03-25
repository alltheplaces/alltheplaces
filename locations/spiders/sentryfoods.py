# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class SentryFoodsSpider(scrapy.Spider):
    name = "sentryfoods"
    item_attributes = {"brand": "Sentry Foods"}
    allowed_domains = ["sentryfoods.com"]
    start_urls = ("https://www.sentryfoods.com/stores/search-stores.html",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath(
            '//div[@class="searchbystate parbase section"]/div/div/*/ul/li/a/@href'
        ).extract()
        for path in city_urls:
            yield scrapy.Request(
                "https://www.sentryfoods.com" + path.strip() + "&displayCount=100",
                callback=self.parse_state,
            )

    def parse_state(self, response):
        response.selector.remove_namespaces()
        store_elems = response.xpath('//div[@class="store-search-results"]/ul/li')
        for store_elem in store_elems:
            url = response.urljoin(
                store_elem.xpath('.//a[@class="store-detail"]/@href').extract_first()
            )
            city_state_zip = store_elem.xpath(
                './/p[@class="store-city-state-zip"]/text()'
            ).extract_first()
            city, state_zip = city_state_zip.split(",", 1)
            state, zipcode = state_zip.split(" ", 1)

            props = {
                "website": url,
                "ref": store_elem.xpath(".//@data-storeid").extract_first(),
                "lat": store_elem.xpath(".//@data-storelat").extract_first(),
                "lon": store_elem.xpath(".//@data-storelng").extract_first(),
                "name": store_elem.xpath(
                    './/h6[@class="store-display-name"]/text()'
                ).extract_first(),
                "addr_full": store_elem.xpath(
                    './/p[@class="store-address"]/text()'
                ).extract_first(),
                "phone": store_elem.xpath('.//p[@class="store-main-phone"]/span/text()')
                .extract_first()
                .strip(),
                "opening_hours": store_elem.xpath(
                    './/ul[@class="store-regular-hours"]/li/text()'
                ).extract_first(),
                "city": city,
                "state": state,
                "postcode": zipcode,
            }
            yield GeojsonPointItem(**props)
