from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class NinetynineCentsOnlyUSSpider(SitemapSpider, StructuredDataSpider):
    name = "99_cents_only_us"
    item_attributes = {"brand": "99 Cents Only Stores", "brand_wikidata": "Q4646294"}
    sitemap_urls = ["https://locations.99only.com/robots.txt"]
    sitemap_rules = [(r"/discount-store-\d+.html$", "parse_sd")]
    wanted_types = ["Store"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # The street address has whitespace at the end sometimes
        item["street_address"] = item["street_address"].strip()
        item["branch"] = item.pop("name").removesuffix(" Store Near You")

        yield item
