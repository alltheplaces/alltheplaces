from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class NoodlesAndCompanyUSSpider(SitemapSpider, StructuredDataSpider):
    name = "noodles_and_company_us"
    item_attributes = {"brand": "Noodles and Company", "brand_wikidata": "Q7049673"}
    sitemap_urls = ["https://locations.noodles.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/locations\.noodles\.com\/[^/]+/[^/]+/(?!delivery)[a-z0-9-]+$", "parse_sd")]
