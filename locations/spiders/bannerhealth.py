# -*- coding: utf-8 -*-
import scrapy
import re
import json

from locations.items import GeojsonPointItem


class BannerHealthSpider(scrapy.Spider):
    name = "bannerhealth"
    item_attributes = {"brand": "Banner Health"}
    allowed_domains = ["bannerhealth.com"]
    start_urls = ("https://www.bannerhealth.com/locations?PageNo=ALL",)

    def parse(self, response):
        urls = response.xpath('//div[@class="location-link"][2]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        try:
            locs = response.xpath(
                '//div[@class="text-card-location-image-content"]/p[1]/text()[2]'
            ).extract_first()
            city, state_postalcode = locs.split(",")
            state_postalcode = state_postalcode.strip()
            jsondata = json.loads(
                response.xpath(
                    '//div[@data-js="map_canvas-v2"]/@data-map-config'
                ).extract_first()
            )
            data = jsondata["markerList"]
            name = re.search(
                r".+/(.+)",
                response.xpath('//meta[@property="og:url"]/@content').extract_first(),
            ).group(1)
            ref = re.search(r".+/(.+)", response.url).group(1)

            if " " in state_postalcode:
                state, postcode = state_postalcode.split(" ")
                state = state.strip()
                postcode = postcode.strip()
            else:
                state = state_postalcode
                postcode = None

            for locations in data:
                location = json.dumps(locations)
                location_data = json.loads(location)

            properties = {
                "ref": ref,
                "name": name,
                "addr_full": response.xpath(
                    '//div[@class="text-card-location-image-content"]/p[1]/text()'
                ).extract_first(),
                "city": city,
                "state": state,
                "postcode": postcode,
                "phone": response.xpath(
                    '//li[@class="text-card-location-image-content-action-list-item"][1]/a/text()'
                )
                .extract_first()
                .strip(),
                "lat": float(location_data["Latitude"]),
                "lon": float(location_data["Longitude"]),
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
        except:
            pass
