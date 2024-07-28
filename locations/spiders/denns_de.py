from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DennsDESpider(SitemapSpider, StructuredDataSpider):
    name = "denns_de"
    item_attributes = {
        "brand": "Denns BioMarkt",
        "brand_wikidata": "Q48883773",
    }
    allowed_domains = ["www.biomarkt.de"]
    sitemap_urls = ["https://www.biomarkt.de/sitemap/sitemap-index.xml"]
    sitemap_rules = [(r"(.+)/marktseite$", "parse_sd")]
    wanted_types = ["Store"]
