from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ChildcareNetworkUSSpider(SitemapSpider, StructuredDataSpider):
    name = "childcare_network_us"
    item_attributes = {"brand": "Childcare Network", "brand_wikidata": "Q121356406"}
    sitemap_urls = ["https://schools.childcarenetwork.com/robots.txt"]
    sitemap_rules = [(r"\.com/\w\w/[-\w]+/[-\w]+$", "parse_sd")]
    wanted_types = ["ChildCare"]
