# -*- coding: utf-8 -*-
import scrapy

from locations.linked_data_parser import LinkedDataParser


class FandangoSpider(scrapy.spiders.SitemapSpider):
    name = "fandango"
    download_delay = 0.25
    sitemap_urls = ["https://www.fandango.com/robots.txt"]
    sitemap_follow = [r"theaters"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; CrOS aarch64 14909.100.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    }

    def parse(self, response):
        item = LinkedDataParser.parse(response, "MovieTheater")
        item["brand"] = item["ref"]
        slug = response.url.split("/")[-2]
        item["ref"] = slug.split("-")[-1]
        return item
