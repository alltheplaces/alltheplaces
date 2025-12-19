from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CibcCASpider(SitemapSpider, StructuredDataSpider):
    name = "cibc_ca"
    item_attributes = {"brand": "CIBC", "brand_wikidata": "Q666694"}
    sitemap_urls = ["https://locations.cibc.com/sitemap-index.xml.gz"]
    sitemap_rules = [(r"https://locations\.cibc\.com/\w\w/.+/\d+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["street_address"] != "CLOSED":
            apply_category(Categories.BANK, item)
            yield item
