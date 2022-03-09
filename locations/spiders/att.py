import scrapy
import json
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}


class ATTScraper(scrapy.Spider):
    name = "att"
    item_attributes = {"brand": "AT&T", "brand_wikidata": "Q35476"}
    allowed_domains = ["www.att.com"]
    start_urls = ("https://www.att.com/stores/us",)
    download_delay = 0.2

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
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H%M"
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        urls = response.xpath('//a[@class="Directory-listLink"]/@href').extract()
        is_store_list = response.xpath('//a[@class="Teaser-titleLink"]/@href').extract()

        if not urls and is_store_list:
            urls = response.xpath('//a[@class="Teaser-titleLink"]/@href').extract()
        for url in urls:
            if url.count("/") >= 2:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(url))

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        properties = {
            "ref": ref,
            "name": response.xpath(
                'normalize-space(//span[@class="LocationName-brand"]/text())'
            ).extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//meta[@itemprop="streetAddress"]/@content)'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//meta[@itemprop="addressLocality"]/@content)'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//abbr[@itemprop="addressRegion"]/text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]/text())'
            ).extract_first(),
            "country": response.xpath(
                'normalize-space(//abbr[@itemprop="addressCountry"]/text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]//text())'
            ).extract_first(),
            "website": response.url,
            "lat": response.xpath(
                'normalize-space(//meta[@itemprop="latitude"]/@content)'
            ).extract_first(),
            "lon": response.xpath(
                'normalize-space(//meta[@itemprop="longitude"]/@content)'
            ).extract_first(),
        }

        hours = response.xpath(
            '//span[@class="c-hours-today js-hours-today"]/@data-days'
        ).extract_first()
        properties["opening_hours"] = self.parse_hours(hours)

        yield GeojsonPointItem(**properties)
