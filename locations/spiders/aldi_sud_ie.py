from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AldiSudIESpider(SitemapSpider, StructuredDataSpider):
    name = "aldi_sud_ie"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171672", "country": "IE"}
    allowed_domains = ["aldi.ie"]
    sitemap_urls = ["https://stores.aldi.ie/sitemap.xml"]
    sitemap_rules = [(r"https://stores\.aldi\.ie/[^/]+/[^/]+/[^/]+$", "parse")]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("ALDI ")

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
