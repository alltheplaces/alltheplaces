# -*- coding: utf-8 -*-
import urllib.parse
from scrapy.spiders import SitemapSpider
from locations.linked_data_parser import LinkedDataParser
from locations.hours import OpeningHours
import json


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
        json_ld = json.loads(
            response.xpath(
                '//script[@id="thd-helmet__script--storeDetailStructuredLocalBusinessData"]/text()'
            ).extract_first()
        )
        item = LinkedDataParser.parse_ld(json_ld)
        item["ref"] = item["website"].split("/")[-1]
        mapurl = urllib.parse.urlsplit(
            response.css('img[alt="map preview"]').attrib["src"]
        )
        lat_lon = next(p for p in mapurl.path.split("/") if "," in p)
        lat, lon = lat_lon.split(",")
        item["lat"] = lat
        item["lon"] = lon
        oh = OpeningHours()
        oh.from_linked_data({"openingHours": json_ld["openingHours"]}, "%I:%M %p")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
