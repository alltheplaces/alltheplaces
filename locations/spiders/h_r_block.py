import scrapy
import re
from locations.items import GeojsonPointItem


class HRBlockSpider(scrapy.Spider):
    name = "h_r_block"
    item_attributes = {"brand": "H&R Block", "brand_wikidata": "Q5627799"}
    allowed_domains = ["www.hrblock.com"]
    download_delay = 0.8
    start_urls = (
        "https://www.hrblock.com/sitemaps/hrb-opp-sitemap.xml",
        "https://www.hrblock.com/sitemaps/ba-opp-sitemap.xml",
    )

    def parse_stores(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        properties = {
            "addr_full": " ".join(
                response.xpath('//span[@itemprop="streetAddress"]/text()').extract()
            ),
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
            "country": response.xpath(
                'normalize-space(//span[@itemprop="addressCountry"]/text())'
            ).extract_first(),
            "ref": ref,
            "website": response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            "lat": response.xpath(
                'normalize-space(//meta[@itemprop="latitude"]/@content)'
            ).extract_first(),
            "lon": response.xpath(
                'normalize-space(//meta[@itemprop="longitude"]/@content)'
            ).extract_first(),
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        response.selector.remove_namespaces()
        locations = response.xpath("//url/loc/text()").extract()

        for location in locations:
            yield scrapy.Request(location, callback=self.parse_stores)
