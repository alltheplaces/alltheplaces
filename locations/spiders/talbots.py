# -*- coding: utf-8 -*-
from datetime import datetime

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class TalbotsSpider(CrawlSpider):
    name = "talbots"
    allowed_domains = ["www.talbots.com"]
    start_urls = ["https://www.talbots.com/view-all-stores/"]
    rules = [
        Rule(LinkExtractor(allow=r"store\?StoreID=(\d+)$"), callback="parse_each_website")
    ]
    item_attributes = {"brand": "Talbots", "brand_wikidata": "Q7679064"}

    def parse_each_website(self, response):
        properties = {
            "ref": response.url,
            "website": response.url,
            "name": self.sanitize_name(
                response.xpath('//*[@id="storedetails-wrapper"]/h1/text()').get()
            ),
            "phone": response.xpath('//*[@id="storePhone"]/a/text()').get(),
            "addr_full": self.get_address(
                response.xpath('//*[@id="storeAddress"]/div/div/div[1]/text()').getall()
            ),
            "opening_hours": self.sanitize_time(
                response.xpath('//*[@id="storeHours"]/div/text()').getall()
            ),
        }
        yield GeojsonPointItem(**properties)

    def get_address(self, response):
        address = []
        for line in response:
            add = line.replace("\n", "")
            if len(add) == 0:
                continue
            if "Phone:" in line:
                break
            address.append(add)
        return ", ".join(address)

    def sanitize_time(self, response):
        opening_hours = OpeningHours()
        for time in response:
            if time in ("\n", "Hours:"):
                continue
            parts = time.split()
            if parts[1] == "CLOSED":
                continue
            dayOfWeek = parts[0][:2]
            opensAt = self.get_24_hr_time(parts[1], parts[2])
            closesAt = self.get_24_hr_time(parts[4], parts[5])
            opening_hours.add_range(dayOfWeek, opensAt, closesAt)
        return opening_hours.as_opening_hours()

    def get_24_hr_time(self, time, meridiem):
        time_12_hr_format = datetime.strptime(time + " " + meridiem, "%I:%M %p")
        return datetime.strftime(time_12_hr_format, "%H:%M")

    def sanitize_name(self, response):
        return response.replace("\n", "")
