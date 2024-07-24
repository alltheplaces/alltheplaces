import json

import scrapy

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature


class BestBuySpider(scrapy.Spider):
    name = "best_buy"
    item_attributes = {"brand": "Best Buy", "brand_wikidata": "Q533415", "extras": Categories.SHOP_ELECTRONICS.value}
    allowed_domains = ["stores.bestbuy.com"]
    start_urls = ("https://stores.bestbuy.com/",)

    def normalize_hours(self, hours):
        o = OpeningHours()

        for hour in hours:
            if not hour.get("holidayHoursIsRegular"):
                continue

            short_day = hour["day"].title()[:2]

            for r in hour["intervals"]:
                open_time = "%04d" % r["start"]
                close_time = "%04d" % r["end"]

                o.add_range(short_day, open_time, close_time, "%H%M")

        return o.as_opening_hours()

    def parse_location(self, response):
        opening_hours = response.css(".js-location-hours").xpath("@data-days").extract_first()
        if opening_hours:
            opening_hours = json.loads(opening_hours)
            opening_hours = self.normalize_hours(opening_hours)

        name = response.xpath('//span[@id="location-name"]/text()').extract_first()
        if not name.strip():
            name = "".join(response.xpath('//span[@id="location-name"]//text()').extract())

        props = {
            "name": name,
            "brand": "Pacific Sales Kitchen & Home" if "Pacific Sales" in name else self.item_attributes["brand"],
            "street_address": response.xpath('//meta[@itemprop="streetAddress"]/@content').extract_first(),
            "lat": float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
            "lon": float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            "city": response.xpath('//span[@class="c-address-city"]/text()').extract_first(),
            "postcode": response.xpath('//span[@class="c-address-postal-code"]/text()').extract_first(),
            "state": response.xpath('//abbr[@class="c-address-state"]/text()').extract_first(),
            "phone": response.xpath(
                '//span[@class="c-phone-number-span c-phone-main-number-span"]/text()'
            ).extract_first(),
            "ref": response.url,
            "website": response.url,
            "opening_hours": opening_hours,
        }
        return Feature(**props)

    def parse(self, response):
        locations = response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').extract()
        if not locations:
            stores = response.xpath('//div[@class="c-LocationGrid"]//a[@class="Link Teaser-titleLink"]/@href').extract()
            if not stores:
                yield self.parse_location(response)
            for store in stores:
                if store.endswith("/magnolia.html"):  # store within a store
                    continue
                yield scrapy.Request(url=response.urljoin(store), callback=self.parse_location)
        else:
            for location in locations:
                yield scrapy.Request(url=response.urljoin(location), callback=self.parse)
