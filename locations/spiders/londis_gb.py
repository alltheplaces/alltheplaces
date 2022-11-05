import scrapy
from locations.open_graph_parser import OpenGraphParser


class LondisGBSpider(scrapy.spiders.SitemapSpider):
    name = "londis_gb"
    item_attributes = {
        "brand": "Londis",
        "brand_wikidata": "Q21008564",
        "country": "GB",
    }
    allowed_domains = ["londis.co.uk"]
    sitemap_urls = ["https://www.londis.co.uk/sitemap.xml"]
    sitemap_rules = [("/our-stores/", "parse_store")]
    download_delay = 1.0

    def parse_store(self, response):
        yield OpenGraphParser.parse(response)
