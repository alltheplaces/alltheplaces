from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class WimpyZASpider(SitemapSpider, StructuredDataSpider):
    name = "wimpy_za"
    item_attributes = {"brand": "Wimpy", "brand_wikidata": "Q2811992"}
    sitemap_urls = ["https://location.wimpy.co.za/robots.txt"]
    sitemap_rules = [(r"location\.wimpy\.co\.za/[-\w()]+$", "parse")]
    search_for_twitter = False

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["image"] = None

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").lstrip(self.item_attributes["brand"]).strip()
        yield item
