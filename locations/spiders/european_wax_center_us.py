from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class EuropeanWaxCenterUSSpider(SitemapSpider, StructuredDataSpider):
    name = "european_wax_center_us"
    item_attributes = {
        "brand_wikidata": "Q5413426",
        "brand": "European Wax Center",
    }
    sitemap_urls = ["https://locations.waxcenter.com/sitemap/sitemap_index.xml"]
    sitemap_rules = [(r"https://locations.waxcenter.com/[^/]+/[^/]+/[^/]+\.html$", "parse_sd")]
