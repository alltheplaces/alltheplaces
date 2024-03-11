from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SocieteGeneraleSpider(SitemapSpider, StructuredDataSpider):
    name = "societe_generale"
    item_attributes = {"brand": "Societé Génerale", "brand_wikidata": "Q270363"}
    allowed_domains = ["societegenerale.com", "agences.sg.fr"]
    sitemap_urls = ["https://agences.societegenerale.fr/banque-assurance/sitemap_agence_pois.xml"]
    sitemap_rules = [("", "parse_sd")]
    download_delay = 0.5
