import re

import scrapy

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.structured_data_spider import StructuredDataSpider


# TODO: turn this into a CrawlSpider
class AvisSpider(StructuredDataSpider):
    name = "avis"
    item_attributes = {"brand": "Avis", "brand_wikidata": "Q791136"}
    download_delay = 0.5
    allowed_domains = ["avis.com"]
    start_urls = ["https://www.avis.com/en/locations/avisworldwide"]
    search_for_image = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath('//meta[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//meta[@itemprop="longitude"]/@content').get()

        item["opening_hours"] = OpeningHours()
        for start_day, end_day, start_time, end_time in re.findall(
            r"(\w{3})(?:\s-\s(\w{3}))?\s(\d+:\d\d\s[APM]+)\s-\s(\d+:\d\d\s[APM]+)",
            response.xpath('//meta[@itemprop="openingHours"]/@content').get(),
        ):
            start_day = sanitise_day(start_day)
            end_day = sanitise_day(end_day)
            if not end_day:
                end_day = start_day
            if start_day:
                item["opening_hours"].add_days_range(
                    day_range(start_day, end_day), start_time, end_time, time_format="%I:%M %p"
                )

        yield item

    def parse_state(self, response):
        urls = response.xpath('//ul[contains(@class, "location-list-ul")]//li/a/@href').extract()

        if not urls:
            urls = set(response.xpath('//ul[contains(@class, "LocContainer")]//a/@href').extract())
            urls = [u for u in urls if "javascript:void" not in u]

        location_list = re.compile("^/en/locations/(?:us|ca|au)/[a-z]{2}/[^/]+$")
        us_single_location = re.compile(r"/en/locations/(?:us|ca|au)/[a-z]{2}/[^/]+/[^/]+$")
        single_location = re.compile(r"/en/locations/(?!us|ca|au)[a-z]{2}/[^/]+/[^/]+$")

        for url in urls:
            if single_location.match(url) or us_single_location.match(url):
                yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)
            elif location_list.match(url):
                # skip these, we get them already
                continue
            elif "xx" in url:
                continue

    def parse_country(self, response):
        urls = response.xpath('//div[contains(@class,"country-wrapper")]//li/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse(self, response):
        urls = response.xpath('//div[@class="wl-location-state"]//li/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_country)
