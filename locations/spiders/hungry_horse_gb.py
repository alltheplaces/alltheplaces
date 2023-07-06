from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HungryHorseGBSpider(SitemapSpider, StructuredDataSpider):
    name = "hungry_horse_gb"
    item_attributes = {"brand": "Hungry Horse", "brand_wikidata": "Q5943510"}
    allowed_domains = ["www.hungryhorse.co.uk"]
    sitemap_urls = ["https://www.hungryhorse.co.uk/xml-sitemap"]
    sitemap_rules = [(r"/pubs/([\w-]+)/([\w-]+)/$", "parse_sd")]
