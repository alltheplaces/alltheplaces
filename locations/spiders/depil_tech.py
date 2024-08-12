from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DepilTechSpider(SitemapSpider, StructuredDataSpider):
    name = "depil_tech"
    item_attributes = {"brand": "Dépil Tech", "brand_wikidata": "Q120762716"}
    allowed_domains = ["www.depiltech.com"]
    sitemap_urls = ["https://www.depiltech.com/sitemap.xml"]
    sitemap_rules = [(r"/fr/[\w-]+/[\w-]+/\d+", "parse_sd")]
    wanted_types = ["HealthAndBeautyBusiness"]
