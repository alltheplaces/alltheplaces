# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class HibachisanSpider(scrapy.Spider):
    name = "hibachisan"
    item_attributes = {"brand": "Hibachisan"}
    allowed_domains = ["hibachisan.com"]
    start_urls = [
        "http://www.hibachisan.com/locations/Default.aspx",
    ]

    def parse(self, response):
        state_list = response.xpath(
            "//select[@id='ctl00_ContentPlaceHolder1_ddlState']/option/@value"
        ).extract()

        for state in state_list:
            if state == "-- SELECT --":
                continue

            url = (
                "http://www.hibachisan.com/locations/locatorresults.aspx?state=" + state
            )
            yield scrapy.Request(response.urljoin(url), callback=self.parse_stores)

    def parse_stores(self, response):
        store_list = response.xpath(
            "//table[@id='ctl00_ContentPlaceHolder1_dlGetStoresByState']/tr/td"
        )

        for store in store_list:
            name = store.xpath(".//div[@class='stateheader']/text()").extract_first()
            ref = response.url + "_" + name.replace(" ", "_")
            phone = store.xpath(
                ".//span[contains(@id,'phoneLabel')]/text()"
            ).extract_first()
            if phone:
                phone = phone.replace("Phone:", "").strip()
            else:
                phone = ""

            properties = {
                "ref": ref,
                "name": name,
                "addr_full": store.xpath(".//span[contains(@id,'addressLabel')]/text()")
                .extract_first()
                .strip(),
                "city": store.xpath(".//span[contains(@id,'cityLabel')]/text()")
                .extract_first()
                .strip(),
                "state": store.xpath(".//span[contains(@id,'stateLabel')]/text()")
                .extract_first()
                .strip(),
                "postcode": store.xpath(".//span[contains(@id,'zipLabel')]/text()")
                .extract_first()
                .strip(),
                "phone": phone,
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)

        next_page = response.xpath(
            "//a[@id='ctl00_ContentPlaceHolder1_btnNext']/@href"
        ).extract_first()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page), callback=self.parse_stores
            )
