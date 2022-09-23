# -*- coding: utf-8 -*-
import re

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class MyDentistGBSpider(CrawlSpider):
    name = "mydentist_uk"
    item_attributes = {
        "brand": "My Dentist",
        "brand_wikidata": "Q65118035",
        "country": "GB",
    }
    allowed_domains = ["mydentist.co.uk"]
    start_urls = ["https://www.mydentist.co.uk/dentists/practices/"]
    rules = [
        Rule(
            link_extractor=LinkExtractor(
                allow=r"https:\/\/www\.mydentist\.co\.uk\/dentists\/practices\/([\w]+)(\/[-\w]+)?(\/[-\w]+)?$",
            ),
        ),
        Rule(
            link_extractor=LinkExtractor(
                allow=r"https:\/\/www\.mydentist\.co\.uk\/dentists\/practices\/([\w]+)\/([-\w]+)\/([-\w]+)\/([-\w]+)$",
            ),
            callback="parse_item",
        ),
    ]

    def parse_item(self, response):
        if response.url.startswith("https://www.mydentist.co.uk/error-pages"):
            return

        root = response.xpath(
            '//body[@itemscope][@itemtype="http://schema.org/LocalBusiness"]'
        )

        item = GeojsonPointItem()

        item["lat"] = re.search(r"\"_readModeLat\":(-?[\d.]+),", response.text).group(1)
        item["lon"] = re.search(r"\"_readModeLon\":(-?[\d.]+),", response.text).group(1)

        item["name"] = root.xpath('.//span[@itemprop="name"]/text()').get()

        address = root.xpath('.//div[@itemprop="address"][@itemscope]')
        item["street_address"] = address.xpath(
            './/span[@itemprop="streetAddress"]/text()'
        ).get()
        item["city"] = root.xpath('.//span[@itemprop="addressLocality"]/text()').get()
        item["state"] = root.xpath('.//span[@itemprop="addressLocality"]/text()').get()
        item["postcode"] = root.xpath('.//span[@itemprop="postalCode"]/text()').get()

        item["phone"] = root.xpath('.//span[@itemprop="telephone"]/a/@href').get()
        if item.get("phone"):
            item["phone"] = item["phone"].replace("tel:", "")

        item["email"] = root.xpath('.//span[@itemprop="email"]/a/@href').get()
        if item.get("email"):
            item["email"] = item["email"].replace("mailto:", "")

        item["website"] = response.url

        oh = OpeningHours()
        for rule in root.xpath('.//time[@itemprop="openingHours"]/@datetime').getall():
            day, times = rule.split(" ")
            open_time, close_time = times.split("-")
            oh.add_range(day[:2], open_time, close_time)

        item["opening_hours"] = oh.as_opening_hours()

        item["ref"] = response.url

        yield item
