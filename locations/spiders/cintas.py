# -*- coding: utf-8 -*-
import re
import json

import scrapy

from locations.items import GeojsonPointItem


class CintasSpider(scrapy.Spider):
    # download_delay of 0.0 results in rate limiting and 403 errors.
    download_delay = 0.2
    name = "cintas"
    item_attributes = {"brand": "Cintas", "brand_wikidata": "Q1092571"}
    allowed_domains = ["cintas.com"]
    start_urls = ("https://www.cintas.com/local/usa",)

    def parse(self, response):
        urls = response.xpath('//ul[@class="col-3 group locations"]//a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        facilityurls = response.xpath('//ul[@id="accordion"]//a/@href').extract()
        for facilityurl in facilityurls:
            yield scrapy.Request(
                response.urljoin(facilityurl), callback=self.parse_store
            )

    def parse_store(self, response):
        try:
            data = json.loads(
                response.xpath(
                    '//script[@type="application/ld+json" and contains(text(), "addressLocality")]/text()'
                ).extract_first()
            )
            store = (
                data["address"]["streetAddress"]
                + ",%20"
                + data["address"]["addressLocality"]
                + ",%20"
                + data["address"]["addressRegion"]
            )

            storeurl = "https://www.cintas.com/sitefinity/public/services/locationfinder.svc/search/{}/25".format(
                store
            )
            yield scrapy.Request(response.urljoin(storeurl), callback=self.parse_loc)
        except:
            pass

    def parse_loc(self, response):
        try:
            geocoderdata = response.xpath("//body//text()").extract()
            geocodertext = geocoderdata[0]
            geocodertext = geocodertext.replace("[", "")
            geocode_re = re.search("distance(.*)", geocodertext).group()
            for item in geocode_re.split('"location":'):
                geocode_replace = re.sub('"distance":.*?:{', "", item)
                geocode_replace = geocode_replace.replace("}", "")
                geocode_replace = geocode_replace.replace("{", "")
                geocode_replace = geocode_replace.replace("]", "")
                geocode_replace = geocode_replace.replace("'", "")
                geocode_replace = geocode_replace.replace('"', "")
                if item.startswith("dist"):
                    pass
                else:
                    geoc_list = geocode_replace.split(",")

                    properties = {
                        "ref": geoc_list[5].replace("Id:", ""),
                        "name": "Cintas",
                        "addr_full": geoc_list[0].replace("Address_1:", ""),
                        "city": geoc_list[2].replace("City:", ""),
                        "state": geoc_list[4].replace("District:", ""),
                        "postcode": geoc_list[10].replace("Postal:", ""),
                        "country": "US",
                        "phone": geoc_list[12].replace("Phone:", ""),
                        "lat": float(geoc_list[6].replace("Latitude:", "")),
                        "lon": float(geoc_list[7].replace("Longitude:", "")),
                    }

                    yield GeojsonPointItem(**properties)
        except:
            pass
