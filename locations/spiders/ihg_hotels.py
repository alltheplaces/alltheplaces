import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.open_graph_parser import OpenGraphParser


class IHGHotelsSpider(scrapy.spiders.SitemapSpider):
    name = "ihg_hotels"
    allowed_domains = ["ihg.com"]
    sitemap_urls = ["https://www.ihg.com/bin/sitemapindex.xml"]
    sitemap_rules = [(r".*/us/en/.*/hoteldetail$", "parse")]
    download_delay = 0.5

    my_brands = {
        "armyhotels": ("Army Hotels", "Q16994722"),
        "avidhotels": ("Avid Hotels", "Q60749907"),
        "candlewood": ("Candlewood Suites", "Q5032010"),
        "crowneplaza": ("Crowne Plaza", "Q2746220"),
        "evenhotels": ("Even Hotels", "Q5416522"),
        "holidayinn": ("Holiday Inn", "Q2717882"),
        "holidayinnclubvacations": None,
        "holidayinnexpress": ("Holiday Inn Express", "Q5880423"),
        "holidayinnresorts": None,
        "hotelindigo": ("Hotel Indigo", "Q5911596"),
        "intercontinental": ("InterContinental", "Q1825730"),
        "kimptonhotels": ("Kimpton", "Q6410248"),
        "regent": ("Regent", "Q3250375"),
        "spnd": None,
        "staybridge": ("Staybridge Suites", "Q7605116"),
        "vignettecollection": None,
        "voco": ("Voco Hotels", "Q60750454"),
    }

    def parse(self, response):
        if "/destinations" in response.url:
            return

        hotel_type = response.url.split("/")[3]
        brand = self.my_brands.get(hotel_type)
        if not brand:
            self.logger.error("no brand/dispatch for: %s / %s", hotel_type, response.url)
            return

        if hotel_type in ["hotelindigo"]:
            item = OpenGraphParser.parse(response)
        else:
            item = LinkedDataParser.parse(response, "Hotel")

        if item:
            item["ref"] = response.url
            item["brand"], item["brand_wikidata"] = brand
            yield item
