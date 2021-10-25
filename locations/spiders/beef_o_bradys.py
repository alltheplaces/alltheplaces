# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class BeefOBradysSpider(scrapy.Spider):
    name = "beef_o_bradys"
    allowed_domains = ['locationstogo.com']

    start_urls = [
        'https://locationstogo.com/beefs/pinsNearestBeefs.ashx?lat1=32.475&lon1=-96.99&range=5000&fullbar=%25&partyroom=%25&catering=%25&breakfast=%25&onlineordering=%25&delivery=%25&type=zip+code++&term=76065',
    ]

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for place in data:
            properties = {
                'ref': place["storeID"],
                'name': place["title"],
                'addr_full': place["address"],
                'city': place["city"],
                'state': place["state"],
                'postcode': place["zip"],
                'lat': place["lat"],
                'lon': place["lng"],
                'phone': place["phone"],
                'website': "https://www.beefobradys.com/" + place["url"]
            }

            yield GeojsonPointItem(**properties)

    # allowed_domains = ['beefobradys.com']

    # start_urls = [
    #     'https://www.beefobradys.com/sitemap.aspx',
    # ]
    #
    # def parse(self, response):
    #     urls = response.xpath('//*[@class="sublinkgroup locs"]/div/p/a/@href').extract()
    #
    #     for url in urls:
    #         yield scrapy.Request(url, callback=self.parse_places)
    #
    # def parse_hours(self, hours):
    #     opening_hours = OpeningHours()
    #
    #     for hour in hours:
    #
    #         if "CLOSED" in hour:
    #             pass
    #         else:
    #             day = re.search(r'^[a-zA-Z]{2}', hour).group(0)
    #             hour = hour.replace(day, "")
    #
    #             opening, closing = hour.split(" - ")
    #
    #             opening = opening.strip()
    #             closing = closing.strip()
    #
    #             if " " in opening:
    #                 opening = opening.replace(" ", "")
    #             if " " in closing:
    #                 closing = closing.replace(" ", "")
    #
    #             opening_hours.add_range(day=day,
    #                                     open_time=opening,
    #                                     close_time=closing,
    #                                     time_format='%I:%M%p'
    #                                     )
    #
    #     return opening_hours.as_opening_hours()
    #
    # def parse_places(self, response):
    #     properties = {
    #         'ref': re.search(r'.+/(.+?)/?(?:\.html|$)', response.url).group(1),
    #         'name': response.xpath('//*[@id="MainContent_lblTitle"]/text()').extract_first(),
    #         'addr_full': response.xpath('//*[@id="MainContent_lblStreetAddress"]/text()').extract_first(),
    #         'city': response.xpath('//*[@id="MainContent_lblCity"]/text()').extract_first(),
    #         'state': response.xpath('//*[@id="MainContent_lblState"]/text()').extract_first(),
    #         'postcode': response.xpath('//*[@id="MainContent_lblZip"]/text()').extract_first(),
    #         'country': response.xpath('//*[@itemprop="addressCountry"]/@value').extract_first(),
    #         'phone': response.xpath('//*[@id="MainContent_lblPhone"]/a/text()').extract_first(),
    #         'website': response.url
    #     }
    #
    #     hours = self.parse_hours(response.xpath('//*[@itemprop="openingHours"]/@content').extract())
    #     if hours:
    #         properties["opening_hours"] = hours
    #
    #     yield GeojsonPointItem(**properties)

    # start_urls = [
    #     'https://locationstogo.com/beefs/pinsNearestBeefs.ashx?lat1=32.475&lon1=-96.99&range=100&fullbar=%25&partyroom=%25&catering=%25&breakfast=%25&onlineordering=%25&delivery=%25&type=zip+code++&term=76065',
    # ]

    # def start_requests(self):
    #     base_url = "https://locationstogo.com/beefs/pinsNearestBeefs.ashx?lat1={lat}&lon1={lng}&range=100&fullbar=%25&partyroom=%25&catering=%25&breakfast=%25&onlineordering=%25&delivery=%25"
    #     with open('./locations/searchable_points/us_centroids_100mile_radius.csv') as points:
    #         next(points)
    #         for point in points:
    #             _, lat, lon = point.strip().split(',')
    #             url = base_url.format(lat=lat, lng=lon)
    #             yield scrapy.Request(url=url,
    #                                  callback=self.parse)

    # def parse(self, response):
    #     data = json.loads(response.body_as_unicode())
    #
    #     for place in data:
    #         properties = {
    #             'ref': place["storeID"],
    #             'name': place["title"],
    #             'addr_full': place["address"],
    #             'city': place["city"],
    #             'state': place["state"],
    #             'postcode': place["zip"],
    #             'lat': place["lat"],
    #             'lon': place["lng"],
    #             'phone': place["phone"],
    #             'website': "https://www.beefobradys.com/" + place["url"]
    #         }
    #
    #         yield GeojsonPointItem(**properties)
