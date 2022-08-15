# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser
from locations.google_url import url_to_coords


def extract_google_position(item, response):
    for link in response.xpath("//img/@src").extract():
        if link.startswith("https://maps.googleapis.com/maps/api/staticmap"):
            item["lat"], item["lon"] = url_to_coords(link)
            return


def set_located_in(item, located_in, located_in_wikidata):
    item["located_in"] = located_in
    item["located_in_wikidata"] = located_in_wikidata


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
            if "-tesco" in response.url:
                set_located_in(item, "Tesco Extra", "Q25172225")
            extract_google_position(item, response)
            return item
