import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}


class UpsStoreSpider(scrapy.Spider):
    name = "upsstore"
    item_attributes = {"brand": "UPS Store", "brand_wikidata": "Q7771029"}
    allowed_domains = ["theupsstore.com"]
    download_delay = 0.1
    start_urls = ("https://locations.theupsstore.com/",)

    def parse_hours(self, hours):
        """
        :param hours:
        :return:
        """
        hours = json.loads(hours)
        o = OpeningHours()

        for day in hours["hours"]["days"]:
            if not day["isClosed"]:
                interval = day["intervals"][0]

                o.add_range(
                    DAY_MAPPING[day["day"]],
                    open_time=str(interval["start"]),
                    close_time=str(interval["end"]),
                    time_format="%H%M",
                )
        return o.as_opening_hours()

    def parse_store(self, response):
        if "Permanently Closed" in response.text:
            return

        ref = response.xpath('//input[@id="store_id"]/@value').extract_first()
        if not ref:
            ref = re.search(
                r"store(\d+)@theupsstore.com",
                response.xpath('//a[@itemprop="email"]/text()').extract_first(),
            ).group(0)

        properties = {
            "name": response.xpath('//span[@class="LocationName-geo"]/text()').extract_first(),
            "phone": response.xpath('//span[@itemprop="telephone"]/text()').extract_first(),
            "addr_full": response.xpath('//meta[@itemprop="streetAddress"]/@content').extract_first(),
            "city": response.xpath('//meta[@itemprop="addressLocality"]/@content').extract_first(),
            "state": response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            "country": response.xpath('//abbr[@itemprop="addressCountry"]/text()').extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
            "lon": float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
        }

        hours = response.xpath('//script[@id="location_info_hours"]/text()').extract_first()
        try:
            hours = self.parse_hours(hours)
            if hours:
                properties["opening_hours"] = hours
        except Exception:
            pass

        yield Feature(**properties)

    def parse(self, response):
        urls = response.xpath('//a[@class="Directory-listLink"]/@href').extract()

        if urls:
            for url in urls:
                if len(url.split("/")) == 3:
                    callback = self.parse_store
                else:
                    callback = self.parse

                yield scrapy.Request(
                    response.urljoin(url),
                    callback=callback,
                )

        else:
            urls = response.xpath('//a[@class="Link"]/@href').extract()
            for url in urls:
                yield scrapy.Request(
                    response.urljoin(url),
                    callback=self.parse_store,
                )
