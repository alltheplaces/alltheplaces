from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TerranovaSpider(SitemapSpider, StructuredDataSpider):
    name = "terranova"
    item_attributes = {"brand": "Terranova", "brand_wikidata": "Q93585264"}
    sitemap_urls = ["https://store.terranovastyle.com/sitemap.xml"]
    sitemap_rules = [("/en/", "parse_sd")]
    wanted_types = ["ClothingStore"]
