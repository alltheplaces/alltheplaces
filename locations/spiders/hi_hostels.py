import re

import scrapy

from locations.items import Feature


class HiHostelsSpider(scrapy.Spider):
    name = "hi_hostels"
    item_attributes = {"brand": "Hi Hostels", "brand_wikidata": "Q1608722"}
    allowed_domains = ["hihostels.com"]
    start_urls = ("https://www.hihostels.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        regex = re.compile(r"http\S+hihostels.com/\S+/hostels/\S+")
        for path in city_urls:
            if not re.search(regex, path):
                pass
            else:
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):
        properties = {
            "name": " ".join(
                response.xpath("/html/body/div[1]/div[6]/div[2]/div[1]/h1/span/text()").extract()[0].split()
            ),
            "ref": " ".join(
                response.xpath("/html/body/div[1]/div[6]/div[2]/div[1]/h1/span/text()").extract()[0].split()
            ),
            "addr_full": " ".join(
                response.xpath("/html/body/div[1]/div[6]/div[2]/div[1]/div[2]/p[1]/text()")
                .extract()[0]
                .split(",")[0]
                .split()
            ),
            "city": " ".join(
                response.xpath("/html/body/div[1]/div[6]/div[2]/div[1]/div[2]/p[1]/text()")
                .extract()[0]
                .split(",")[1]
                .split()
            ),
            "postcode": " ".join(
                response.xpath("/html/body/div[1]/div[6]/div[2]/div[1]/div[2]/p[1]/text()")
                .extract()[0]
                .split(",")[-2]
                .split()
            ),
            "country": " ".join(
                response.xpath("/html/body/div[1]/div[6]/div[2]/div[1]/div[2]/p[1]/text()")
                .extract()[0]
                .split(",")[-1]
                .split()
            ),
            "website": response.xpath('//head/link[@rel="canonical"]/@href').extract_first(),
            "lon": float(response.xpath('//*[@id ="lon"]/@value').extract()[0]),
            "lat": float(response.xpath('//*[@id ="lat"]/@value').extract()[0]),
        }

        yield Feature(**properties)
