import json

import scrapy
from scrapy import Request

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

REGIONS = ["americas", "emea", "apac"]


class NatixisSpider(StructuredDataSpider):
    name = "natixis"
    item_attributes = {"brand": "Natixis", "brand_wikidata": "Q571156"}
    start_urls = ["https://home.cib.natixis.com/locations"]
    wanted_types = ["FinancialService"]

    def parse(self, response, **kwargs):
        a_href_urls = response.xpath('//a[contains(@href, "cib.natixis.com")]/@href').getall()
        for url in a_href_urls:
            good_url = False
            for region in REGIONS:
                if f"{region}.cib.natixis.com" in url:
                    good_url = True
                    break
            if good_url:
                yield Request(url=url, callback=self.parse_sd, meta={"url": url})

    def post_process_item(self, item, response, ld_data):
        country = response.url.split("/")[-1].replace("-", " ").title()
        if country == "En":
            country = response.url.split("/")[-2].replace("-", " ").title()

        item["country"] = country
        apply_category(Categories.BANK, item)
        yield item
