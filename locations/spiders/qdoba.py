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


class QdobaSpider(scrapy.Spider):
    name = "qdoba"
    item_attributes = {"brand": "Qdoba", "brand_wikidata": "Q1363885"}
    allowed_domains = ["qdoba.com"]
    start_urls = (
        "https://locations.qdoba.com/us.html",
        "https://locations.qdoba.com/ca.html",
    )

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        store_data = json.loads(store_hours)

        for store_day in store_data:
            if len(store_day["intervals"]) < 1:
                continue
            day = DAY_MAPPING[store_day["day"]]
            open_time = str(store_day["intervals"][0]["start"])
            if open_time == "0":
                open_time = "0000"
            close_time = str(store_day["intervals"][0]["end"])
            if close_time == "0":
                close_time = "2359"
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H%M")

        return opening_hours.as_opening_hours()

    def parse(self, response):
        urls = response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').extract()
        is_store_list = response.xpath('//a[@class="location-card-visit"]/@href').extract()
        is_resturant_page = response.xpath('//main[@itemtype="http://schema.org/Restaurant"]').extract_first()

        if is_resturant_page:
            yield scrapy.Request(response.url, callback=self.parse_store)
        else:
            if not urls and is_store_list:
                for store_url in is_store_list:
                    yield scrapy.Request(response.urljoin(store_url), callback=self.parse_store)

            for url in urls:
                yield scrapy.Request(response.urljoin(url), dont_filter=True)

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        properties = {
            "ref": ref,
            "name": response.xpath('normalize-space(//span[@class="location-name-brand"]/text())').extract_first(),
            "street_address": response.xpath(
                'normalize-space(//span[@class="c-address-street-1"]/text())'
            ).extract_first(),
            "city": response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            "state": response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]/text())').extract_first(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            "country": response.xpath('normalize-space(//abbr[@itemprop="addressCountry"]/text())').extract_first(),
            "phone": response.xpath('normalize-space(//span[@itemprop="telephone"]//text())').extract_first(),
            "website": response.url,
            "lat": response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first(),
            "lon": response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first(),
        }

        hours = response.xpath('//span[@class="c-location-hours-today js-location-hours"]/@data-days').extract_first()
        if hours:
            properties["opening_hours"] = self.parse_hours(hours)

        yield Feature(**properties)
