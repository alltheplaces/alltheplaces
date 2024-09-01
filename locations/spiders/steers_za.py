from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SteersZASpider(SitemapSpider, StructuredDataSpider):
    name = "steers_za"
    item_attributes = {"brand": "Steers", "brand_wikidata": "Q3056765"}
    sitemap_urls = ["https://location.steers.co.za/robots.txt"]
    sitemap_rules = [(r"location\.steers\.co\.za/[-\w()]+$", "parse")]
    search_for_twitter = False

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["image"] = None

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").lstrip(self.item_attributes["brand"]).strip()
        yield item
