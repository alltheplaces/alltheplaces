from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AmericanFreightSpider(SitemapSpider, StructuredDataSpider):
    name = "american_freight"
    item_attributes = {"brand": "American Freight", "brand_wikidata": "Q94360971"}
    sitemap_urls = ["https://www.americanfreight.com/sitemap.xml"]
    sitemap_rules = [(r"/store/", "parse_sd")]
    wanted_types = ["DepartmentStore"]
    requires_proxy = True
