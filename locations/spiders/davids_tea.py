from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DavidsTeaSpider(SitemapSpider, StructuredDataSpider):
    name = "davids_tea"
    item_attributes = {"brand": "David's Tea", "brand_wikidata": "Q3019129"}
    allowed_domains = [
        "locations.davidstea.com",
    ]
    sitemap_urls = ["https://locations.davidstea.com/robots.txt"]
    sitemap_rules = [("", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        yield item
