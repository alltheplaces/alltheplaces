from scrapy.spiders import SitemapSpider

from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import StructuredDataSpider


class ShoeZoneGB(SitemapSpider, StructuredDataSpider):
    name = "shoezone_gb"
    item_attributes = {
        "brand": "Shoe Zone",
        "brand_wikidata": "Q7500016",
        "country": "GB",
    }
    sitemap_urls = ["https://www.shoezone.com/sitemap_stores.xml"]
    sitemap_rules = [(r"https:\/\/www\.shoezone\.com\/Stores\/[-._\w]+-(\d+)$", "parse_sd")]
    wanted_types = ["ShoeStore"]

    def inspect_item(self, item, response):
        item["street_address"] = clean_address(item["street_address"])

        yield item
