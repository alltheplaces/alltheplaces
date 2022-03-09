import scrapy
import re
from locations.items import GeojsonPointItem


class BigLotsSpider(scrapy.Spider):

    name = "biglots"
    item_attributes = {"brand": "Big Lots"}
    allowed_domains = ["local.biglots.com"]
    download_delay = 0.5
    start_urls = ("http://local.biglots.com/",)

    def parse_stores(self, response):
        properties = {
            "addr_full": response.xpath(
                'normalize-space(//span[@itemprop="streetAddress"]/text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]/text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]/text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//span[@itemprop="addressRegion"]/text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]/text())'
            ).extract_first(),
            "ref": re.findall(r"[0-9]+", response.url)[0],
            "website": response.url,
            "lat": float(
                response.xpath('normalize-space(//meta[@name="geo.position"]/@content)')
                .extract_first()
                .split(";")[0]
                .strip()
            ),
            "lon": float(
                response.xpath('normalize-space(//meta[@name="geo.position"]/@content)')
                .extract_first()
                .split(";")[1]
                .strip()
            ),
        }
        hours = response.xpath('//meta[@itemprop="openingHours"]/@content').extract()
        hours = "; ".join(hours)
        if hours:
            properties["opening_hours"] = hours
        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath(
            '//ul[@id="results_list"]/li/div[@class="result clearfix"]/h2/a/@href'
        ).extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        city_urls = response.xpath('//div[@class="column"]/div/ul/li/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(
                response.urljoin(path), callback=self.parse_city_stores
            )

    def parse(self, response):
        urls = response.xpath('//div[@id="states"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
