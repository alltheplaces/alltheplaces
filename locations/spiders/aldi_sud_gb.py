from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AldiSudGB(SitemapSpider, StructuredDataSpider):
    name = "aldi_sud_gb"
    item_attributes = {"brand_wikidata": "Q41171672", "country": "GB"}
    allowed_domains = ["aldi.co.uk"]
    sitemap_urls = ["https://stores.aldi.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https://stores\.aldi\.co\.uk/[^/]+/[^/]+/[^/]+$", "parse")]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("ALDI ")

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
