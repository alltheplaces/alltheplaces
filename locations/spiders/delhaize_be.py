from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class DelhaizeBESpider(SitemapSpider, StructuredDataSpider):
    name = "delhaize_be"
    item_attributes = {"brand": "Delhaize", "brand_wikidata": "Q1184173", "extras": Categories.SHOP_SUPERMARKET.value}
    sitemap_urls = ["https://stores.delhaize.be/sitemap.xml"]
    sitemap_rules = [("/fr/", "parse_sd")]
