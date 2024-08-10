from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ChampionUSSpider(SitemapSpider, StructuredDataSpider):
    name = "champion_us"
    item_attributes = {"brand": "Champion", "brand_wikidata": "Q2948688"}
    sitemap_urls = ["https://stores.champion.com/robots.txt"]
    sitemap_rules = [(r"/\w\w/[-\w]+/[-\w]+\.html", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name", None)
        yield item
