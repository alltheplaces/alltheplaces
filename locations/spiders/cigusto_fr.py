from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CigustoFRSpider(SitemapSpider, StructuredDataSpider):
    name = "cigusto_fr"
    item_attributes = {"brand": "Cigusto", "brand_wikidata": "Q120785690"}
    sitemap_urls = ["https://www.cigusto.com/sitemap.xml"]
    sitemap_rules = [("/magasins/magasin-", "parse_sd")]
