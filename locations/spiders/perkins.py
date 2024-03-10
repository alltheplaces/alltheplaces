
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PerkinsSpider(SitemapSpider, StructuredDataSpider):
    name = "perkins"
    item_attributes = {"brand": "Perkins", "brand_wikidata": "Q7169056"}
    allowed_domains = ["www.perkinsrestaurants.com"]
    sitemap_urls = ("https://www.perkinsrestaurants.com/sitemap.xml",)
    sitemap_rules = [
        # Example: https://www.perkinsrestaurants.com/locations/us/mn/winona/956-1-2-mankoto-avenue
        (r"/locations/.*$", "parse_sd")
    ]
    time_format = "%I:%M"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url
        return super().post_process_item(item, response, ld_data, **kwargs)
