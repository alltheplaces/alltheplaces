from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ApplebeesSpider(SitemapSpider, StructuredDataSpider):
    name = "applebees"
    item_attributes = {"brand_wikidata": "Q621532"}
    sitemap_urls = ["https://restaurants.applebees.com/robots.txt"]
    sitemap_rules = [(r"https://restaurants\.applebees\.com/en-us/\w\w/[-\w]+/[-.\w]+\d+$", "parse_sd")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None

        yield item
