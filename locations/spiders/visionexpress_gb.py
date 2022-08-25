# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser
from locations.google_url import extract_google_position


class VisionExpressGBSpider(scrapy.spiders.SitemapSpider):
    name = "visionexpress_gb"
    item_attributes = {
        "brand": "VisionExpress",
        "brand_wikidata": "Q7936150",
    }
    sitemap_urls = ["https://www.visionexpress.com/sitemap.xml"]
    sitemap_rules = [("/opticians/", "parse")]
    download_delay = 0.2

    def parse(self, response):
        item = LinkedDataParser.parse(response, "Store")
        if item:
            item["street_address"] = item["street_address"].replace(" undefined", "")
            # TODO: when there is an agreed solution to this.
            # if "-tesco" in response.url:
            #    set_located_in(item, "Tesco Extra", "Q25172225")
            extract_google_position(item, response)
            return item
