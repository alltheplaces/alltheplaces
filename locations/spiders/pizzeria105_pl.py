from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class Pizzeria105PlSpider(SitemapSpider, StructuredDataSpider):
    name = "pizzeria_105_pl"
    allowed_domains = ["105.pl"]
    item_attributes = {"brand": "Pizzeria 105", "brand_wikidata": "Q123090276"}
    sitemap_urls = ["https://105.pl/sitemap.xml"]
    sitemap_rules = [(r"https://105.pl/pizzeria-.*", "parse_sd")]
