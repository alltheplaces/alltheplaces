# -*- coding: utf-8 -*-
import scrapy
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class MarksAndSpencerSpider(scrapy.Spider):
    name = "waterstones"
    item_attributes = {"brand": "Waterstones"}
    allowed_domains = ["www.waterstones.com"]
    start_urls = ("https://www.waterstones.com/bookshops/viewall",)

    def parse(self, response):
        stores = response.xpath(
            '//div[contains(@class, "shops-directory-list")]//a/@href'
        ).extract()
        stores = set(stores)
        for store in stores:
            yield response.follow(store, self.parse_store)

        next_page = response.xpath('//link[@rel="next"]/@href').extract_first()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_store(self, response):
        properties = {
            "ref": response.url.split("/")[4],
            "name": self.get_meta_property(response, "og:title"),
            "addr_full": self.get_meta_property(
                response, "business:contact_data:street_address"
            ),
            "city": self.get_meta_property(response, "business:contact_data:locality"),
            "postcode": self.get_meta_property(
                response, "business:contact_data:postal_code"
            ),
            "lat": self.get_meta_property(response, "place:location:latitude"),
            "lon": self.get_meta_property(response, "place:location:longitude"),
            "phone": self.get_meta_property(
                response, "business:contact_data:phone_number"
            ),
            "opening_hours": self.get_opening_hours(response),
            "website": response.url,
        }
        yield GeojsonPointItem(**properties)

    def get_meta_property(self, response, property):
        return response.xpath(
            f'//meta[@property="{property}"]/@content'
        ).extract_first()

    def get_opening_hours(self, response):
        days = response.xpath(
            '//meta[@property="business:hours:day"]/@content'
        ).extract()
        starts = response.xpath(
            '//meta[@property="business:hours:start"]/@content'
        ).extract()
        ends = response.xpath(
            '//meta[@property="business:hours:end"]/@content'
        ).extract()
        o = OpeningHours()
        for i in range(len(days)):
            day = days[i][0].upper() + days[i][1]
            start = starts[i].replace(".", ":")
            end = ends[i].replace(".", ":")
            if day and start and end:
                o.add_range(day, start, end)
        return o.as_opening_hours()
