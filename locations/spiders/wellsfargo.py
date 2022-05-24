# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class WellsFargoSpider(scrapy.Spider):
    name = "wellsfargo"
    item_attributes = {"brand": "Wells Fargo", "brand_wikidata": "Q744149"}
    allowed_domains = ["www.wellsfargo.com"]
    start_urls = ("https://www.wellsfargo.com/locator/",)

    def store_hours(self, hours_elem):
        opening_hours = []
        for hours_range in hours_elem.xpath(".//li/text()").extract():
            day_range, time_range = hours_range.split(" ", 1)
            day_range = (
                day_range.replace("Mon", "Mo")
                .replace("Tue", "Tu")
                .replace("Thu", "Th")
                .replace("Fri", "Fr")
                .replace("Sat", "Sa")
                .replace("Sun", "Su")
            )

            if time_range == "closed":
                continue

            match = re.search(
                r"^(\d{2}):(\d{2}) ([AP])M-(\d{2}):(\d{2}) ([AP])M$", time_range
            )
            if not match:
                self.logger.error("Could not parse time_range for %s", time_range)
                continue

            (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

            if f_ampm == "P":
                f_hr = int(f_hr) + 12
            if t_ampm == "P":
                t_hr = int(t_hr) + 12

            time_range = "{:02d}:{:02d}-{:02d}:{:02d}".format(
                int(f_hr),
                int(f_min),
                int(t_hr),
                int(t_min),
            )

            opening_hours.append("{} {}".format(day_range, time_range))

        return "; ".join(opening_hours)

    def parse(self, response):
        area_elems = response.xpath('//map[@id="theImageMap"]/area')
        for area_elem in area_elems:
            area_title = area_elem.xpath(".//@title").extract_first()
            if "currently does not" in area_title:
                continue

            href = area_elem.xpath(".//@href").extract_first()[1:]

            yield scrapy.Request(
                "https://www.wellsfargo.com/locator/as/getCities/" + href,
                callback=self.parse_state,
                meta={
                    "state": href,
                },
            )

    def parse_state(self, response):
        data = json.loads(response.text.strip().split("\n")[2])
        for city in data["allCities"]:
            yield scrapy.Request(
                "https://www.wellsfargo.com/locator/search/?searchTxt={},+{}&mlflg=N&il=EN&bo=1".format(
                    city, response.meta["state"]
                ),
                callback=self.parse_city,
            )

    def parse_city(self, response):
        result_elems = response.xpath(
            '//ul[@id="searchResultsList"]/li[@class="aResult"]'
        )
        for result_elem in result_elems:
            features = result_elem.xpath(".//@data-features").extract_first()
            if "bankOnly" not in features:
                continue

            loc = result_elem.xpath(".//@data-location").extract_first()
            (lat, lon) = map(float, loc.split(","))

            opening_hours = None
            hours_elem = result_elem.xpath('.//ul[@itemprop="itemListElement"]')
            if hours_elem:
                opening_hours = self.store_hours(hours_elem[0])

            yield GeojsonPointItem(
                lat=lat,
                lon=lon,
                addr_full=result_elem.xpath(
                    './/div[@itemprop="addressRegion"]/text()'
                ).extract_first(),
                city=result_elem.xpath(
                    './/span[@itemprop="addressLocality"]/text()'
                ).extract_first(),
                state=result_elem.xpath(
                    './/abbr[@itemprop="addressRegion"]/text()'
                ).extract_first(),
                postcode=result_elem.xpath(
                    './/span[@itemprop="postalCode"]/text()'
                ).extract_first(),
                phone=result_elem.xpath(
                    './/div[@itemprop="telephone"]/text()'
                ).extract_first()[7:],
                ref=result_elem.xpath(
                    './/div[@itemprop="telephone"]/text()'
                ).extract_first()[7:],
                opening_hours=opening_hours,
            )
