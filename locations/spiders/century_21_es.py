import re

import scrapy

from locations.items import GeojsonPointItem


class Century21EsSpider(scrapy.Spider):
    name = "century_21_es"
    item_attributes = {"brand": "Century21", "brand_wikidata": "Q1054480"}
    allowed_domains = ["century21global.com"]
    start_urls = ["https://www.century21global.com/es/agencias-inmobiliarias/Spain?searchtype=office"]

    def parse(self, response):
        agences = response.xpath('//div[contains(@class,"search-col-results")]/div[contains(@class,"search-result")]')
        for agence in agences:
            url = agence.xpath('.//a[contains(@class, "search-result-info")]/@href').get()
            id = re.findall("id=[0-9]*", url)[0].replace("id=", "")
            name = agence.xpath('.//span[contains(@class, "name-label")]/text()').get()
            address = agence.xpath("normalize-space(./a/span[2]/text()[1])").get()
            city_postcode = agence.xpath("normalize-space(./a/span[2]/text()[2])").get()
            postcode = re.findall("[0-9]{5}|[A-Z0-9]{3} [A-Z0-9]{3}", city_postcode)[0]
            city = city_postcode.replace(postcode, "").strip()
            country = agence.xpath("normalize-space(./a/span[2]/text()[3])").get()

            yield GeojsonPointItem(
                name=name,
                ref=id,
                addr_full=address,
                city=city,
                postcode=postcode,
                country=country,
                website=f"https://www.{self.allowed_domains[0]}{url}",
            )

        # Pagination next page
        if response.xpath('//a[contains(@aria-label, "Siguiente")]/@href').get():
            yield scrapy.Request(url=f"https://www.{self.allowed_domains[0]}{next}", callback=self.parse)
