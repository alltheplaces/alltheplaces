import json
import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "SUNDAY": "Su",
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
}


class JCPenneySpider(scrapy.Spider):
    name = "jcpenney"
    item_attributes = {"brand": "JCPenney", "brand_wikidata": "Q920037"}
    allowed_domains = ["jcpenney.com"]
    download_delay = 0.2
    start_urls = ("https://stores.jcpenney.com/",)

    def parse_hours(self, days):
        opening_hours = OpeningHours()
        days = json.loads(days)

        for day in days:
            if not day["intervals"]:
                continue
            opening_hours.add_range(
                day=DAY_MAPPING[day["day"]],
                open_time=str(day["intervals"][0]["start"]),
                close_time=str(day["intervals"][0]["end"]),
                time_format="%H%M",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        urls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()

        if not urls:  # cities with multiple stores
            urls = response.xpath('//li[@class="nearbyLocation"]//a/@href').extract()

        for url in urls:
            if url.endswith(".html"):
                callback = self.parse_store
            else:
                callback = self.parse
            yield scrapy.Request(
                response.urljoin(url),
                callback=callback,
            )

    def parse_store(self, response):

        brand = "JCPenney"
        store = response.xpath('//div[contains(@class," LocationInfo-details")]')
        name = store.xpath('//h1[@id="location-name"]/text()').extract_first()
        name = name.replace("JCPenney Apparel and Accessories", "").strip()

        properties = {
            "ref": re.search(r".*/(.*).html", response.url).groups()[0],
            "name": name,
            "lat": float(
                store.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                store.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "phone": store.xpath('//span[@id="telephone"]/text()').extract_first(),
            "addr_full": store.xpath(
                '//span[@class="c-address-street-1"]/text()'
            ).extract_first(),
            "city": store.xpath(
                '//span[@class="c-address-city"]/text()'
            ).extract_first(),
            "state": store.xpath(
                '//abbr[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": store.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "brand": brand,
        }

        hours = store.xpath(
            '//div[contains(@class, "js-location-hours")]/@data-days'
        ).extract_first()
        if hours:
            properties["opening_hours"] = self.parse_hours(hours)

        yield GeojsonPointItem(**properties)
