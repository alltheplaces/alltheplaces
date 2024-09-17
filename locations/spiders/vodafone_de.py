import json

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

VODAFONE_SHARED_ATTRIBUTES = {"brand": "Vodafone", "brand_wikidata": "Q122141"}


class VodafoneDESpider(scrapy.Spider):
    name = "vodafone_de"
    item_attributes = VODAFONE_SHARED_ATTRIBUTES
    allowed_domains = ["vodafone.de"]
    start_urls = ["https://shops.vodafone.de"]

    def parse(self, response):
        urls = response.xpath('//a[@class="Directory-listLink"]/@href')
        for url in urls:
            yield scrapy.Request(url=response.urljoin(url.get()), callback=self.parse_store)

    def parse_store(self, response):
        oh = OpeningHours()
        days = response.xpath('//div[@id="c-hours-collapse"]/div/@data-days').get()
        if days:
            days = json.loads(days)
            for day in days:
                if day.get("intervals"):
                    start = str(day.get("intervals")[0].get("start")).zfill(4)
                    end = str(day.get("intervals")[0].get("end")).zfill(4)
                    oh.add_range(
                        day=day.get("day"),
                        open_time=f"{start[:2]}:{start[2:]}",
                        close_time=f"{end[:2]}:{end[2:]}",
                    )

        if response.xpath('//h1[@id="location-name"]/span[1]/text()').get():
            if email := response.xpath('//a[@class="Hero-email"]/@href').get():
                email = email.replace("mailto:", "")

            properties = {
                "ref": response.url,
                "street_address": response.xpath('//span[@class="c-address-street-1"]/text()').get(),
                "postcode": response.xpath('//span[@class="c-address-postal-code"]/text()').get(),
                "city": response.xpath('//span[@class="c-address-city"]/text()').get(),
                "phone": response.xpath('//div[contains(@class, "Phone--main")]/div[1]//a/text()').get(),
                "email": email,
                "facebook": response.xpath('//div[@class="Socials-list"]/a[3]/@href').get(),
                "website": response.url,
                "lat": response.xpath('//meta[contains(@itemprop, "latitude")]/@content').get(),
                "lon": response.xpath('//meta[contains(@itemprop, "longitude")]/@content').get(),
                "opening_hours": oh.as_opening_hours(),
            }

            yield Feature(**properties)

        urls = response.xpath('//a[contains(@class, "Teaser-link Teaser-locationLink")]/@href')
        for url in urls:
            yield scrapy.Request(url=response.urljoin(url.get()), callback=self.parse_store)
