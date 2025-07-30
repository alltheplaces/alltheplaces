from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PandoraSpider(SitemapSpider, StructuredDataSpider):
    name = "pandora"
    item_attributes = {"brand": "Pandora", "brand_wikidata": "Q2241604"}
    sitemap_urls = ["https://stores.pandora.net/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/stores\.pandora\.net\/[a-z-0-9]+\/[a-z-0-9]+\/[a-z-0-9]+\/.+html$", "parse_sd")]
    custom_settings = {"REDIRECT_ENABLED": False}
