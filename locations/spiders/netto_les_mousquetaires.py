from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class NettoLesMousquetairesSpider(SitemapSpider, StructuredDataSpider):
    name = "netto_les_mousquetaires"
    item_attributes = {"brand": "Netto", "brand_wikidata": "Q2720988"}
    sitemap_urls = ["https://magasin.netto.fr/sitemap.xml"]
    sitemap_follow = ["locationsitemap"]
    sitemap_rules = [("", "parse_sd")]
