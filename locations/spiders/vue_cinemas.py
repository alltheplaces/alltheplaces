# -*- coding: utf-8 -*-
from urllib import parse
import scrapy
from locations.items import GeojsonPointItem


class VueCinemasSpider(scrapy.Spider):
    name = "vue_cinemas"
    item_attributes = {"brand": "Vue Cinemas"}
    start_urls = ("https://www.myvue.com/data/locations/",)

    def parse(self, response):
        data = response.json()
        for letter in data["venues"]:
            for cinema in letter["cinemas"]:
                yield response.follow(
                    f"https://www.myvue.com/cinema/{cinema['link_name']}/getting-here",
                    self.parse_cinema,
                )

    def parse_cinema(self, response):
        cinema_name = response.xpath(
            '//h2[@class="article-title gradient-fill"]/text()'
        ).extract_first()

        address_parts = response.xpath('//img[@alt="location-pin"]/../text()').extract()
        if not address_parts:
            address_parts = response.xpath(
                f'//div[@class="collapse__heading" and @data-page-url="{parse.urlparse(response.url).path}"]/following-sibling::div//div[@class="container container--scroll"]/div/p/text()'
            ).extract()
        address_parts = [a.strip() for a in address_parts if a.strip()]

        maps_link = response.xpath('//a[text()="Get directions"]/@href').extract_first()
        query_string = parse.urlparse(maps_link).query
        query_dict = parse.parse_qs(query_string)
        coords = query_dict["q"][0].split(",")

        properties = {
            "ref": response.url.split("/")[4],
            "name": cinema_name,
            "addr_full": ", ".join(address_parts),
            "postcode": address_parts[-1],
            "lat": float(coords[0]),
            "lon": float(coords[1]),
            "website": response.url.replace("/getting-here", ""),
        }
        yield GeojsonPointItem(**properties)
