from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CostcoCASpider(SitemapSpider, StructuredDataSpider):
    name = "costco_ca"
    item_attributes = {"name": "Costco", "brand": "Costco", "brand_wikidata": "Q715583"}
    sitemap_urls = ["https://www.costco.ca/robots.txt"]
    sitemap_rules = [("/warehouse-locations/", "parse")]
    wanted_types = ["Store"]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_WHOLESALE, item)
        yield item
