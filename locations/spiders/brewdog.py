# -*- coding: utf-8 -*-
import re
import urllib.parse

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

kHoursRe = re.compile(r"(?P<day>\w+):\s+(?P<open_time>\S+) - (?P<close_time>\S+)")


class BrewdogSpider(scrapy.Spider):
    name = "brewdog"
    item_attributes = {"brand": "BrewDog", "brand_wikidata": "Q911367"}
    allowed_domains = ["www.brewdog.com"]
    start_urls = (
        "https://www.brewdog.com/uk/bar_pages/bar/locator/view_all/1/filter/uk/",
        "https://www.brewdog.com/usa/bar_pages/bar/locator/view_all/1/filter/usa/",
        "https://www.brewdog.com/eu_en/bar_pages/bar/locator/view_all/1/filter/global/",
    )

    def parse(self, response):
        yield from response.follow_all(
            css="a.bar-listing__results__bar__buttons__view", callback=self.parse_bar
        )

    def parse_bar(self, response):
        name = response.xpath('//meta[@name="title"]/@content').extract_first()
        addr = next(
            s
            for s in response.xpath('//div[@id="contact"]//text()').extract()
            if s.strip()
        )

        opening_hours = OpeningHours()
        for row in response.xpath('//div[@id="opening-hours"]/p/text()').extract()[:7]:
            groups = kHoursRe.search(row)
            if groups is None:
                continue
            day = groups["day"][:2]
            opening_hours.add_range(
                day, groups["open_time"], groups["close_time"], "%I:%M%p"
            )

        map_url = response.xpath(
            '//iframe[@class="bar-detail__map"]/@src'
        ).extract_first()
        if map_url:
            query = urllib.parse.urlparse(map_url).query
            [q] = urllib.parse.parse_qs(query)["q"]
            lat, lon = q.split(",")
        else:
            lat = lon = None

        return GeojsonPointItem(
            ref=response.url,
            website=response.url,
            name=name,
            addr_full=addr,
            lat=lat,
            lon=lon,
            opening_hours=opening_hours.as_opening_hours(),
        )
