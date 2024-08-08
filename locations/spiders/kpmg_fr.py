from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KpmgFRSpider(SitemapSpider, StructuredDataSpider):
    name = "kpmg_fr"
    item_attributes = {"brand": "KPMG", "brand_wikidata": "Q493751"}
    allowed_domains = ["bureaux.kpmg.fr"]
    sitemap_urls = ["https://bureaux.kpmg.fr/sitemap_pois.xml"]
    sitemap_rules = [("/details", "parse_sd")]
    wanted_types = ["LegalService", "FinancialService"]
