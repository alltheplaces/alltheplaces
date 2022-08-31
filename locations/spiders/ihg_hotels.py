# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser
from locations.open_graph_parser import OpenGraphParser


def from_wikidata(name, code):
    return {"brand": name, "brand_wikidata": code}


class IHGHotelsSpider(scrapy.spiders.SitemapSpider):
    name = "ihg_hotels"
    allowed_domains = ["ihg.com"]
    sitemap_urls = ["https://www.ihg.com/bin/sitemapindex.xml"]
    sitemap_rules = [(r".*/us/en/.*/hoteldetail$", "parse")]
    download_delay = 0.5

    my_brands = {
        "armyhotels": from_wikidata("Army Hotels", "Q16994722"),
        "avidhotels": from_wikidata("Avid Hotels", "Q60749907"),
        "candlewood": from_wikidata("Candlewood Suites", "Q5032010"),
        "crowneplaza": from_wikidata("Crowne Plaza", "Q2746220"),
        "evenhotels": from_wikidata("Even Hotels", "Q5416522"),
        "holidayinn": from_wikidata("Holiday Inn", "Q2717882"),
        "holidayinnclubvacations": "N/A",
        "holidayinnexpress": from_wikidata("Holiday Inn Express", "Q5880423"),
        "holidayinnresorts": "N/A",
        "hotelindigo": from_wikidata("Hotel Indigo", "Q5911596"),
        "intercontinental": from_wikidata("InterContinental", "Q1825730"),
        "kimptonhotels": from_wikidata("Kimpton", "Q6410248"),
        "regent": from_wikidata("Regent", "Q3250375"),
        "spnd": "N/A",
        "staybridge": from_wikidata("Staybridge Suites", "Q7605116"),
        "vignettecollection": "N/A",
        "voco": from_wikidata("Voco Hotels", "Q60750454"),
    }

    def parse(self, response):
        if "/destinations" in response.url:
            return
        hotel_type = response.url.split("/")[3]
        brand = self.my_brands.get(hotel_type)
        if not brand:
            self.logger.error(
                "no brand/dispatch for: %s / %s", hotel_type, response.url
            )
            return
        if isinstance(brand, str):
            return
        if hotel_type in ["hotelindigo"]:
            item = OpenGraphParser.parse(response)
        else:
            item = LinkedDataParser.parse(response, "Hotel")
        if item:
            item["ref"] = response.url
            item.update(brand)
            yield item
