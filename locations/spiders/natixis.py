import json

import scrapy
from scrapy import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

REGIONS = ["americas", "emea", "apac"]


class NatixisSpider(scrapy.Spider):
    name = "natixis"
    item_attributes = {"brand": "Natixis", "brand_wikidata": "Q571156"}
    start_urls = ["https://home.cib.natixis.com/locations"]

    def parse(self, response, **kwargs):
        a_href_urls = response.xpath('//a[contains(@href, "cib.natixis.com")]/@href').getall()
        for url in a_href_urls:
            good_url = False
            for region in REGIONS:
                if f"{region}.cib.natixis.com" in url:
                    good_url = True
                    break
            if good_url:
                yield Request(url=url, callback=self.parse_country, meta={"url": url})

    def parse_country(self, response):
        country = response.url.split("/")[-1].replace("-", " ").title()
        if country == "En":
            country = response.url.split("/")[-2].replace("-", " ").title()
        shops = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        for shop in shops:
            shop_js = json.loads(shop)
            if shop_js.get("@type") == "WebSite" or shop_js.get("@type") is None:
                continue
            item = DictParser.parse(shop_js)
            item["country"] = country
            item["ref"] = shop_js.get("@id")
            item["street_address"] = shop_js.get("address", {}).get("streetAddress", "")
            item["image"] = shop_js.get("image")
            apply_category(Categories.BANK, item)
            yield item
