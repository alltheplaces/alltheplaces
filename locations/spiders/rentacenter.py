from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class RentacenterSpider(SitemapSpider, StructuredDataSpider):
    name = "rentacenter"
    item_attributes = {"brand": "Rent-A-Center", "brand_wikidata": "Q7313497"}
    allowed_domains = ["rentacenter.com"]

    sitemap_urls = [
        "https://locations.rentacenter.com/sitemap.xml",
    ]
    # Bad:  https://locations.rentacenter.com/nebraska/scottsbluff/69361/
    # Good: https://locations.rentacenter.com/nebraska/scottsbluff/3410-ave-i/
    sitemap_rules = [(r"/[\w-]+/[\w-]+/\d+-[\w\d-]+/$", "parse_sd")]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data):
        ref = ld_data.get("branchCode")
        if not ref:
            return  # not a store page
        item["ref"] = ref

        yield item
