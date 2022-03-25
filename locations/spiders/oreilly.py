# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class OreillyAuto(scrapy.Spider):

    name = "oreilly"
    item_attributes = {"brand": "O'Reilly Auto Parts", "brand_wikidata": "Q7071951"}
    download_delay = 0.2
    allowed_domains = (
        "locations.oreillyauto.com",
        "www.oreillyauto.com",
    )
    start_urls = ("https://www.oreillyauto.com/locations",)

    def parse_hours(self, hours):
        reversed_hours = {}

        if not hours:
            return ""
        hours = [hr for hr in hours if hr.strip() != "-"]
        for day_hour in zip(*[iter(hours)] * 3):
            short_day, from_hr, to_hr = (
                day_hour[0].title()[:2],
                day_hour[1],
                day_hour[2],
            )

            short_frm_hr = from_hr.replace("AM", "").strip()
            hour, minute = to_hr.replace("PM", "").strip().split(":")
            short_to_hr = "{}:{}".format(str(int(hour) + 12), minute)

            final_day_hour = "{}-{}".format(short_frm_hr, short_to_hr)

            reversed_hours.setdefault(final_day_hour, [])
            reversed_hours[final_day_hour].append(short_day)

        if len(reversed_hours) == 1 and list(reversed_hours)[0] == "00:00-24:00":
            return "24/7"

        opening_hours = []

        for key, value in reversed_hours.items():
            if len(value) == 1:
                opening_hours.append("{} {}".format(value[0], key))
            else:
                opening_hours.append("{}-{} {}".format(value[0], value[-1], key))

        return "; ".join(opening_hours)

    def parse_stores(self, response):

        hours = response.xpath(
            '//tr[@class="c-location-hours-details-row js-day-of-week-row highlight-text"]//text()'
        ).extract()
        opening_hours = self.parse_hours(hours)

        props = {
            "addr_full": response.xpath(
                '//span[@class="c-address-street-1"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//span[@class="c-phone-number-span c-phone-main-number-span"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//span[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "ref": response.url,
            "website": response.url,
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "opening_hours": opening_hours,
        }

        return GeojsonPointItem(**props)

    def parse_city_stores(self, response):

        stores = response.xpath('//a[@class="js-fas-details-link"]/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):

        city_urls = response.xpath('//div[@class="filter_item"]/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(
                response.urljoin(path), callback=self.parse_city_stores
            )

    def parse(self, response):

        urls = response.xpath('//div[@class="filter_item"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
