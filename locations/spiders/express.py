import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class ExpressSpider(scrapy.Spider):
    name = "express"
    item_attributes = {"brand": "Express", "brand_wikidata": "Q1384784"}
    allowed_domains = ["stores.express.com", "stores.expressfactoryoutlet.com"]
    start_urls = (
        "https://stores.express.com/us",
        "https://stores.express.com/cr",
        "https://stores.express.com/gt",
        "https://stores.express.com/pa",
        "https://stores.express.com/sv",
        "https://stores.express.com/mx",
        "https://stores.express.com/pr",
        "https://stores.expressfactoryoutlet.com/us",
        "https://stores.expressfactoryoutlet.com/pr",
    )

    def parse_hours(self, hours):
        o = OpeningHours()

        for h in hours:
            try:
                day, open, close = re.search(r"(.{2})\s([\d:]+)-([\d:]+)", h).groups()
                o.add_range(day, open_time=open, close_time=close, time_format="%H:%M")
            except AttributeError:
                continue

        return o.as_opening_hours()

    def parse_stores(self, response):
        ref = re.findall(r"[^(\/)]+$", response.url)
        if len(ref) > 0:
            ref = ref[0].split(".")[0]
        properties = {
            "name": response.xpath('//h1[contains(@class, "Hero-subTitle")]/text()').extract_first(),
            "street_address": response.xpath('//meta[@itemprop="streetAddress"]/@content').extract_first(),
            "phone": response.xpath('normalize-space(//div[@itemprop="telephone"]/text())').extract_first(),
            "city": response.xpath('//meta[@itemprop="addressLocality"]/@content').extract_first(),
            "state": response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            "country": response.xpath('//abbr[@itemprop="addressCountry"]/text()').extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            "lon": float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
            "brand": response.xpath('//h1[@itemprop="name"]/text()')
            .extract_first()
            .replace(" - Temporarily Closed", ""),
        }

        hours = response.xpath('//tr[@itemprop="openingHours"]/@content').extract()
        if hours:
            opening_hours = self.parse_hours(hours)
            if opening_hours:
                properties["opening_hours"] = opening_hours

        apply_category(Categories.SHOP_CLOTHES, properties)
        yield Feature(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//li[@class="Directory-listTeaser"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse(self, response):
        urls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()
        for path in urls:
            pattern = re.compile(r"^[a-z]{2}\/[^()\/]+$")
            pattern1 = re.compile(r"^[a-z]{2}\/[^()]+\/[^()]+\/[^()]+$")
            if pattern.match(path.strip("./")):
                yield scrapy.Request(response.urljoin(path))
            elif pattern1.match(path.strip("./")):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
