import scrapy
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DennsDeSpider(SitemapSpider, StructuredDataSpider):
    name = "denns_de"
    allowed_domains = ["www.biomarkt.de"]
    sitemap_urls = ["https://www.biomarkt.de/sitemap.xml"]
    sitemap_rules = [(r"(.+)/marktseite$", "parse_sd")]
    wanted_types = ["Store"]

    def _parse_sitemap(self, response):
        for row in super()._parse_sitemap(response):
            yield scrapy.Request(
                row.url.replace("http://localhost:8000/", "https://www.biomarkt.de/"), callback=self.parse_sd
            )
