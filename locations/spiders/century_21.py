import re

import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class Century21Spider(scrapy.spiders.SitemapSpider):
    name = "century_21"
    item_attributes = {"brand": "Century 21", "brand_wikidata": "Q1054480"}
    allowed_domains = ["century21global.com"]
    sitemap_urls = ["https://www.century21global.com/sitemap.xml"]
    sitemap_rules = [("/real-estate-offices/", "parse")]

    def parse(self, response):
        country = response.url.split("?")[0].split("/")[-1].replace("-", " ")
        agences = response.xpath('//div[contains(@class,"search-col-results")]/div[contains(@class,"search-result")]')
        for agence in agences:
            url = agence.xpath('.//a[contains(@class, "search-result-info")]/@href').get()
            id = re.findall("id=[0-9]*", url)[0].replace("id=", "")
            name = agence.xpath('.//span[contains(@class, "name-label")]/text()').get()
            address = merge_address_lines(agence.xpath("./a/span[2]/text()").getall())
            lat = agence.xpath(".//@data-lat").get()
            lon = agence.xpath(".//@data-lng").get()

            yield Feature(
                name=name,
                ref=id,
                addr_full=address,
                country=country,
                lat=lat,
                lon=lon,
                website=f"https://www.{self.allowed_domains[0]}{url}",
            )

        # Pagination next page
        if next := response.xpath('//a[contains(@aria-label, "Next")]/@href').get():
            yield scrapy.Request(url=response.urljoin(next), callback=self.parse)
