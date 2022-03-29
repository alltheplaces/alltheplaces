# -*- coding: utf-8 -*-
import scrapy
import re
import json
from locations.items import GeojsonPointItem


class McDonaldsEGSpider(scrapy.Spider):

    name = "mcdonalds_eg"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.eg"]
    start_urls = ("http://www.mcdonalds.eg/ar/stores/page/228",)

    def normalize_time(self, time_str, flag=False):
        match = re.search(r"([0-9]{1,2}):([0-9]{1,2})", time_str)
        h, m = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if flag and int(h) < 13 else int(h),
            int(m),
        )

    def store_hours(self, response):
        response = '<div id="mapInfo" style="width: 200px;">' + response
        selector = scrapy.Selector(text=response)
        opening_hours = selector.xpath(
            '//*[@id="mapInfo"]/div/span[4]/text()'
        ).extract_first()
        if not opening_hours:
            return None
        opening_hours = opening_hours.strip()
        match = re.search(
            r" ([0-9]{1,2}:[0-9]{1,2}).*([0-9]{1,2}:[0-9]{1,2})", opening_hours
        )
        if not match:
            return None
        start, end = match.groups()
        start = self.normalize_time(start)
        end = self.normalize_time(end, True)

        return "Mo-Fr {}-{}".format(start, end)

    def parse_data(self, response):
        response = '<div id="mapInfo" style="width: 200px;">' + response
        selector = scrapy.Selector(text=response)
        name = (
            selector.xpath('//h2[@class="store-title"]/b/text()')
            .extract_first()
            .strip()
        )
        address = (
            selector.xpath('//*[@id="mapInfo"]/div/span[1]/text()')
            .extract_first()
            .strip()
        )
        phone = selector.xpath('//span[@class="store-tel"]/text()').extract_first()
        phone = phone.strip() if phone else ""
        return name, address, phone

    def parse(self, response):
        match = re.search(r"var locS = (\[.*\])\;", response.text)
        results = json.loads(match.groups()[0])
        index = 0
        for data in results:
            data = data.replace("''", '""')
            try:
                store = json.loads(data)
            except Exception as e:
                continue

            name, address, phone = self.parse_data(store[0])

            properties = {
                "ref": index,
                "addr_full": address,
                "phone": phone,
                "name": name,
                "lat": store[1],
                "lon": store[2],
            }

            opening_hours = self.store_hours(store[0])
            if opening_hours:
                properties["opening_hours"] = opening_hours
            index = index + 1
            yield GeojsonPointItem(**properties)
