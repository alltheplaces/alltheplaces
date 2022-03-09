# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from scrapy.selector import Selector


class CareOneSpider(scrapy.Spider):
    name = "care_one"
    allowed_domains = ["care-one.com"]
    start_urls = ("https://www.care-one.com/locations/",)

    def parse(self, response):
        pois = response.xpath(
            '//script[@type="text/javascript" and contains(text(), "locations_results.push")]/text()'
        ).extract()

        for poi in pois:
            address = (
                Selector(text=poi).xpath('//p[@class="\\\'museo"]/text()').extract()
            )
            city_state_postcode = address[-2].split(", ")
            info = Selector(text=poi).xpath("//p/text()").get().split("\n")
            geo = info[1].split("new result_node(")[1].split(",")
            lat = float(geo[0].strip("'"))
            lon = float(geo[1].strip().strip("'"))

            properties = {
                "ref": int(info[2].split(", ")[0]),
                "website": Selector(text=poi).xpath("//a/@href").get().strip("\\'"),
                "name": Selector(text=poi).xpath("//h6/text()").get(),
                "addr_full": ", ".join(address[:-1]),
                "city": city_state_postcode[0],
                "state": city_state_postcode[1].split()[0],
                "postcode": city_state_postcode[1].split()[1],
                "country": "US",
                "phone": address[-1],
                "lat": lat,
                "lon": lon,
            }

            yield GeojsonPointItem(**properties)
