import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class LaneBryantSpider(scrapy.Spider):
    name = "lanebryant"
    item_attributes = {"brand": "Lane Bryant", "brand_wikidata": "Q6485350"}
    allowed_domains = ["stores.lanebryant.com"]

    def start_requests(self):
        states = [
            "al",
            "ak",
            "az",
            "ar",
            "ca",
            "co",
            "ct",
            "dc",
            "de",
            "fl",
            "ga",
            "hi",
            "id",
            "il",
            "in",
            "ia",
            "ks",
            "ky",
            "la",
            "me",
            "md",
            "ma",
            "mi",
            "mn",
            "ms",
            "mo",
            "mt",
            "ne",
            "nv",
            "nh",
            "nj",
            "nm",
            "ny",
            "nc",
            "nd",
            "oh",
            "ok",
            "or",
            "pa",
            "ri",
            "sc",
            "sd",
            "tn",
            "tx",
            "ut",
            "vt",
            "va",
            "wa",
            "wv",
            "wi",
            "wy",
        ]

        base_url = "https://stores.lanebryant.com/{state}"

        for state in states:
            url = base_url.format(state=state)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for group in hours:
            if "Closed" in group:
                pass
            else:
                days, open_time, close_time = re.search(r"([a-zA-Z,]+)\s([\d:]+)-([\d:]+)", group).groups()
                days = days.split(",")
                for day in days:
                    opening_hours.add_range(
                        day=day,
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H:%M",
                    )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        urls = response.xpath(
            '//*[@class="Directory-listItem"]/a/@href | //*[@class="Directory-listTeaser"]/article/h2/a/@href'
        ).extract()

        if len(urls) == 0:
            properties = {
                "name": response.xpath('//*[@class="Core-geomodifier"]/text()').extract_first(),
                "street_address": response.xpath('//*[@class="c-address-street-1"]/text()').extract_first(),
                "city": response.xpath('//*[@class="c-address-city"]/text()').extract_first(),
                "state": response.xpath('//*[@class="c-address-state"]/text()').extract_first(),
                "postcode": response.xpath('//*[@class="c-address-postal-code"]/text()').extract_first(),
                "phone": response.xpath('//*[@id="phone-main"]/text()').extract_first(),
                "ref": "_".join(re.search(r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups()),
                "website": response.url,
                "lat": response.xpath('//*[@itemprop="latitude"]/@content').extract_first(),
                "lon": response.xpath('//*[@itemprop="longitude"]/@content').extract_first(),
            }

            hours = self.parse_hours(response.xpath('//*[@itemprop="openingHours"]/@content').extract())
            if hours:
                properties["opening_hours"] = hours

            yield Feature(**properties)
        else:
            for path in urls:
                yield scrapy.Request(url=response.urljoin(path), callback=self.parse)
