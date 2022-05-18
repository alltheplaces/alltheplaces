import scrapy
import re
from locations.items import GeojsonPointItem


class MicrosoftSpider(scrapy.Spider):
    name = "microsoft"
    item_attributes = {"brand": "Microsoft", "brand_wikidata": "Q2283"}
    allowed_domains = ["www.microsoft.com"]
    download_delay = 0.5
    start_urls = ("https://www.microsoft.com/en-us/store/locations/all-locations",)

    def parse_stores(self, response):

        properties = {
            "name": response.xpath(
                "normalize-space(//h1/strong/text())"
            ).extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//div[@itemprop="streetAddress"]/span/text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//div[@itemprop="telephone"]/span/text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]/text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//span[@itemprop="addressRegion"]/text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]/text())'
            )
            .extract_first()
            .replace("\xa0", ""),
            "country": re.search(r"^(?:[^\/]*\/){3}([^\/]*)", response.url)
            .group(1)
            .lstrip("en-")
            .upper(),
            "ref": re.search(r"\/store-([0-9]+)", response.url).group(1),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//ul[@instancename="Cities list"]/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
