# -*- coding: utf-8 -*-
import scrapy


def country_from_url(response):
    return response.url.split("/")[2].split(".")[-1].upper()


class McDonaldsBalticsSpider(scrapy.spiders.SitemapSpider):
    name = "mcdonalds_baltics"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    sitemap_urls = [
        "https://mcdonalds.ee/location-sitemap.xml",
#        "https://mcd.lt/location-sitemap.xml",
#        "https://mcdonalds.lv/location-sitemap.xml",
    ]

    def parse(self, response):
        print(response.url)


#        item = Brand.MCDONALDS.item(response)
#        item["country"] = country_from_url(response)
#        item["lat"] = response.xpath("//@data-lat").extract_first()
#        item["lon"] = response.xpath("//@data-lng").extract_first()
