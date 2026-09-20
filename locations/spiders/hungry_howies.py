from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HungryHowiesSpider(SitemapSpider, StructuredDataSpider):
    name = "hungry_howies"
    item_attributes = {"brand": "Hungry Howie's", "brand_wikidata": "Q16985303", "name": "Hungry Howie's"}
    allowed_domains = ["hungryhowies.com", "www.hungryhowies.com"]
    sitemap_urls = ["https://www.hungryhowies.com/sitemap.xml"]
    sitemap_rules = [(r"/location/hungry-howie-s-pizza-", "parse_sd")]
    search_for_twitter = False
    search_for_facebook = False
    requires_proxy = True
    # The site sits behind a Cloudflare managed challenge that intermittently
    # 403s legitimate requests too; retrying gets most of them through.
    custom_settings = {"RETRY_TIMES": 5, "RETRY_HTTP_CODES": [403, 429, 500, 502, 503, 504]}

    def post_process_item(self, item, response, ld_data, **kwargs):
        del item["name"]  # generic "Hungry Howie's" on every page, backfilled from item_attributes
        del item["image"]  # same brand logo on every page
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "pizza"
        yield item
