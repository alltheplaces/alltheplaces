from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class NewSeasonsMarketUSSpider(SitemapSpider, StructuredDataSpider):
    name = "new_seasons_market_us"
    item_attributes = {"brand": "New Seasons Market", "brand_wikidata": "Q7011463"}
    sitemap_urls = ["https://www.newseasonsmarket.com/robots.txt"]
    sitemap_rules = [(r"/find-a-store/[\w-]+$", "parse_sd")]
    wanted_types = ["GroceryStore"]
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = response.xpath('//h1[@class="h2"]/text()').get()

        yield item
