# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem

base_url = "https://www.elclubdelamilanesa.com/"


class MilanesaSpider(scrapy.Spider):
    name = "milanesa"
    item_attributes = {"brand": "Club Milanesa"}
    allowed_domains = ["www.elclubdelamilanesa.com"]
    start_urls = ["https://www.elclubdelamilanesa.com/caba.html"]

    def parse(self, response):
        stores = response.xpath('//*[@id="stores-address"]/footer/a[1]/@href').extract()
        for store in stores:
            store = base_url + store
            yield scrapy.Request(store, callback=self.parse_store)

        continued_urls = []
        next_page_url = response.xpath(
            '//*[@id="nav-delivery"]//descendant::*/@href'
        ).extract()
        for i in next_page_url:
            absolute_next_page = base_url + i
            continued_urls.append(absolute_next_page)

        next_page = continued_urls.index(response.url) + 1
        if next_page < len(continued_urls):
            yield scrapy.Request(continued_urls[next_page], callback=self.parse)

    def convert_days(self, days):
        # lun mar mié jue vie sáb dom / mon - sun

        span_eng = {
            "lun": "Mo",
            "mar": "Tu",
            "mié": "We",
            "jue": "Th",
            "vie": "Fr",
            "sáb": "Sa",
            "dom": "Su",
        }

        days = days.split(" A ")
        days = [x.lower() for x in days]

        for k, v in span_eng.items():
            if days[0] == k:
                days[0] = v
            elif days[1] == k:
                days[1] = v

        days = days[0] + " - " + days[1]
        return days

    def parse_store(self, response):
        ref = response.xpath(
            '//*[@id="profile"]/p/span[1]/span[3]/text()'
        ).extract_first()

        street = response.xpath(
            '//*[@id="profile"]/p/span[1]/span[2]/text()'
        ).extract_first()

        city = response.xpath(
            '//*[@id="profile"]/p/span[1]/span[4]/text()'
        ).extract_first()

        # Fix for "C?rdoba"
        city = city.replace("�", "o")

        postcode = response.xpath(
            '//*[@id="profile"]/p/span[1]/span[5]/text()'
        ).extract_first()

        country = response.xpath(
            '//*[@id="profile"]/p/span[1]/span[6]/text()'
        ).extract_first()

        name = (
            response.xpath('//*[@id="profile"]/p/span[1]/span[1]/a/text()')
            .extract_first()
            .strip()
        )

        phone = response.xpath(
            '//*[@id="profile"]/p/span[2]/a/span/text()'
        ).extract_first()

        days = self.convert_days(
            response.xpath('//*[@id="profile"]/p/span[3]/text()')
            .extract_first()
            .strip("Abierto ")
            .split(": ")[0]
        )

        hours = (
            response.xpath('//*[@id="profile"]/p/span[3]/text()')
            .extract_first()
            .strip("Abierto ")
            .split(": ")[1]
        )

        address = "{} {}, {}, {}".format(
            street,
            city,
            country,
            postcode,
        )

        opening_hours = "{} : {}".format(days, hours)

        name = "elclubdelamilanesa - " + name

        yield GeojsonPointItem(
            name=name,
            addr_full=address,
            street=street,
            city=city,
            postcode=postcode,
            phone=phone,
            website=response.url,
            opening_hours=opening_hours,
            ref=response.url,
        )
