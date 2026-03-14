from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider


class BestBuySpider(SitemapSpider, StructuredDataSpider):
    name = "best_buy"
    item_attributes = {"brand_wikidata": "Q533415"}
    allowed_domains = ["stores.bestbuy.com"]
    sitemap_urls = ["https://stores.bestbuy.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z]{2}/[\w-]+/[\w-]+.html", "parse_sd")]
    search_for_image = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        if response.css(".closed-banner-header-shop-online"):
            set_closed(item)
        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
