# -*- coding: utf-8 -*-
import urllib.parse
import json
from scrapy.spiders import SitemapSpider
from locations.linked_data_parser import LinkedDataParser
from locations.hours import OpeningHours
from locations.google_url import url_to_coords


class HomeDepotSpider(SitemapSpider):
    name = "homedepot"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["www.homedepot.com"]
    download_delay = 0.2
    sitemap_urls = ("https://www.homedepot.com/sitemap/d/store.xml",)
    sitemap_rules = [
        (r"^https:\/\/www.homedepot.com\/l\/.*\/\d*$", "parse_store"),
    ]

    def parse_store(self, response):
        json_ld = LinkedDataParser.find_linked_data(response, "LocalBusiness")
        item = LinkedDataParser.parse_ld(json_ld)
        item["ref"] = item["website"].split("/")[-1]
        item["lat"], item["lon"] = url_to_coords(
            response.css('img[alt="map preview"]').attrib["src"]
        )
        oh = OpeningHours()
        oh.from_linked_data({"openingHours": json_ld["openingHours"]}, "%I:%M %p")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
