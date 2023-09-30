import scrapy

from locations.open_graph_parser import OpenGraphParser


class PremierGBSpider(scrapy.spiders.SitemapSpider):
    name = "premier_gb"
    item_attributes = {"brand": "Premier", "brand_wikidata": "Q7240340"}
    allowed_domains = ["premier-stores.co.uk"]
    sitemap_urls = ["https://www.premier-stores.co.uk/sitemap.xml"]
    sitemap_rules = [("/our-stores/", "parse_store")]

    def parse_store(self, response):
        yield OpenGraphParser.parse(response)
