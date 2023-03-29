import re

import scrapy

from locations.hours import DAYS_ES, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class MilanesaARSpider(scrapy.Spider):
    name = "milanesa_ar"
    item_attributes = {"brand": "Club Milanesa", "brand_wikidata": "Q117324078"}
    start_urls = ["https://www.elclubdelamilanesa.com/caba.html"]

    def parse(self, response, **kwargs):
        for store in response.xpath('//*[@id="stores-address"]/footer/a[1]/@href').getall():
            yield response.follow(store, callback=self.parse_store)

        for page in response.xpath('//article[contains(., "ZONAS")]//a/@href').getall():
            yield response.follow(page)

    def parse_store(self, response, **kwargs):
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["name"] = response.xpath("//title/text()").get()
        item["street_address"] = response.xpath('//span[@class="street-address"]/text()').get()
        item["city"] = response.xpath('//span[@class="locality"]/text()').get()
        item["state"] = response.xpath('//span[@class="region"]/text()').get()
        item["postcode"] = response.xpath('//span[@class="postal-code"]/text()').get()
        item["country"] = response.xpath('//span[@class="country"]/text()').get()

        extract_phone(item, response)

        if m := re.search(
            r"(\w+) A (\w+): (\d\d:\d\d) - (\d\d:\d\d)", response.xpath('//span[@class="notes"]/text()').get()
        ):
            start_day = sanitise_day(m.group(1), DAYS_ES)
            end_day = sanitise_day(m.group(2), DAYS_ES)
            if start_day and end_day:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(day_range(start_day, end_day), m.group(3), m.group(4))

        yield item
