from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CaptainDSpider(SitemapSpider, StructuredDataSpider):
    name = "captain_d"
    item_attributes = {"brand": "Captain D's", "brand_wikidata": "Q5036616"}
    sitemap_urls = ["https://locations.captainds.com/robots.txt"]
    sitemap_rules = [(r"https://locations.captainds.com/ll/US/\w{2}/[-\w]+/[-\w]+", "parse_sd")]
    json_parser = "chompjs"
