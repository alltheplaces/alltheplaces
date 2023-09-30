from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class EmberInnsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "ember_inns_gb"
    item_attributes = {"brand": "Ember Inns", "brand_wikidata": "Q116272278"}
    sitemap_urls = ["https://www.emberinns.co.uk/robots.txt"]
    sitemap_rules = [(r"/nationalsearch/\w+/[-\w]+$", "parse_sd")]
