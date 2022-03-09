# -*- coding: utf-8 -*-
import re
import json

import scrapy

from locations.items import GeojsonPointItem


class SonestaSpider(scrapy.Spider):
    download_delay = 0.2
    name = "sonesta"
    item_attributes = {"brand": "Sonesta"}
    allowed_domains = ["sonesta.com"]
    start_urls = ("https://www.sonesta.com",)

    def parse(self, response):
        url = "https://www.sonesta.com/page-data/destinations/page-data.json"
        yield scrapy.Request(response.urljoin(url), callback=self.parse_links)

    def parse_links(self, response):
        xml = scrapy.selector.Selector(response)
        text_json = xml.xpath("//text()").extract()
        dest_json = json.loads(json.dumps(text_json))
        urls = []
        matches = re.findall('.path":{"alias":"(.+?)"}.', dest_json[0])
        for i in matches:
            if ':"en' in i:
                pass
            elif i == "/select":
                pass
            elif i == "us/massachusetts/newton/customer-care":
                pass
            else:
                urls.append(i)
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_loc)

    def parse_loc(self, response):
        dest = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "longitude")]/text()'
        ).extract_first()
        jdata = json.loads(json.dumps(dest))
        try:
            region = re.search('.Region":"(.+?)",.', jdata).group(1)
        except:
            region = ""
        try:
            postal = re.search('.postalCode":(.+?)",.', jdata).group(1).strip('"')
        except:
            postal = ""
        try:
            phone = re.search('.telephone":"(.+?)",.', jdata).group(1)
        except:
            phone = ""

        properties = {
            "ref": re.search('.url":"(.+?)",.', jdata).group(1),
            "name": re.search('.name":"(.+?)",.', jdata).group(1),
            "addr_full": re.search('.streetAddress":"(.+?)",.', jdata).group(1),
            "city": re.search('.Locality":"(.+?)",.', jdata).group(1),
            "state": region,
            "postcode": postal,
            "country": re.search('.Country":"(.+?)"}.', jdata).group(1),
            "phone": phone,
            "lat": float(re.search('.latitude":(.+?),"longitude.', jdata).group(1)),
            "lon": float(re.search('.longitude":(.+?)}.', jdata).group(1)),
        }

        yield GeojsonPointItem(**properties)
