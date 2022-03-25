# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from scrapy.selector import Selector


class HabitBurgerSpider(scrapy.Spider):
    name = "habit-burger"
    allowed_domains = ["habitburger.com"]
    start_urls = ("https://www.habitburger.com/locations/all/",)

    def parse(self, response):
        regions = response.xpath("//h2").xpath("@id").extract()
        non_us_cities = ["phnom penh", "shanghai", "hangzhou"]

        for region in regions:
            region_body = response.xpath(
                '//h2[@id = "{region}"]/following-sibling::ul[@class = "reglist"]'.format(
                    region=region
                )
            ).get()
            pois = Selector(text=region_body).css(".loc").extract()

            for poi in pois:
                ref = Selector(text=poi).xpath("//a/@href").extract()[0].split("/")[-1]
                name = Selector(text=poi).xpath("//h4/text()").extract()
                if name == []:
                    name = Selector(text=poi).xpath("//h3/text()").extract()
                name = "".join(name)

                map_link = (
                    Selector(text=poi)
                    .xpath('//div[@class = "locaddress"]/a')
                    .xpath("@href")
                    .extract_first()
                )
                lat, long = None, None
                if "daddr" in map_link:
                    coords = map_link.split("daddr=")[1].split(",")
                    lat = coords[0]
                    long = coords[1]

                addr = (
                    Selector(text=poi)
                    .xpath('//div[@class = "locaddress"]/a')
                    .extract_first()
                )
                addr = Selector(text=addr).xpath("//a/text()").extract()
                addr = [a.strip() for a in addr]

                addr_full = ", ".join(addr)
                street = ", ".join(addr[:-1])
                city, state, postcode = None, None, None

                if region in ["cambodia", "china"]:
                    for c in non_us_cities:
                        if c in poi.lower():
                            city = c.capitalize()
                    country = region.capitalize()
                else:
                    city = addr[-1].split(", ")[0]
                    state_postcode = addr[-1].split(", ")[1].split(" ")
                    if len(state_postcode) > 1:
                        state = state_postcode[0]
                        postcode = state_postcode[1]
                    country = "US"

                phone = Selector(text=poi).xpath('//div[@class="locinfo"]/text()').get()
                phone = phone.strip() if phone else None
                opening_hours = (
                    Selector(text=poi).xpath('//div[@class="lochrs"]/text()').extract()
                )
                opening_hours = opening_hours = (
                    ", ".join([hours.strip() for hours in opening_hours])
                    if opening_hours
                    else None
                )

                properties = {
                    "ref": ref,
                    "website": "https://www.habitburger.com/locations/" + ref,
                    "name": name,
                    "addr_full": addr_full,
                    "street": street,
                    "city": city,
                    "state": state,
                    "postcode": postcode,
                    "country": country,
                    "phone": phone,
                    "opening_hours": opening_hours,
                    "lat": lat,
                    "lon": long,
                }

                yield GeojsonPointItem(**properties)
