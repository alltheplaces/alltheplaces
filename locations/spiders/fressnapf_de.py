from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FressnapfDESpider(SitemapSpider, StructuredDataSpider):
    name = "fressnapf_de"
    item_attributes = {"brand": "Fressnapf", "brand_wikidata": "Q875796"}
    sitemap_urls = ["https://www.fressnapf.de/sitemap-store.xml"]
