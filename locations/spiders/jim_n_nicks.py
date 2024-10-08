import re

import scrapy

from locations.items import Feature


class JimNNicksSpider(scrapy.Spider):
    name = "jim_n_nicks"
    allowed_domains = ["www.jimnnicks.com"]
    item_attributes = {"brand": "Jim 'N Nick's", "brand_wikidata": "Q122955601"}
    start_urls = ("https://www.jimnnicks.com/locations/",)

    def parse(self, response):
        urls = response.xpath('//ul[@class="directory-links"]/li/a/@href').extract()

        for url in urls:
            if url.count("/") >= 6:
                yield scrapy.Request(url, self.parse_location)
            else:
                yield scrapy.Request(url)

    def parse_location(self, response):
        is_actually_store_list = response.xpath('//ul[@class="directory-links"]/li/a/@href').extract()

        if is_actually_store_list:
            for url in is_actually_store_list:
                yield scrapy.Request(url, self.parse_location)
        else:  # Collect the data
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
            complete_address = response.xpath("//address/text()").extract()
            street_address = complete_address[0]
            city, state_postal = complete_address[-1].split(",")
            state, postal = state_postal.strip().split()

            properties = {
                "ref": ref,
                "name": response.xpath("//h1/text()").extract_first().strip(),
                "street_address": street_address,
                "city": city,
                "state": state,
                "postcode": postal,
                "country": "US",
                "phone": response.xpath('//div[@class="elementor-shortcode"]/a/text()[1]').extract_first(),
                "website": response.url,
            }

            yield Feature(**properties)
