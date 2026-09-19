from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class JetsPizzaSpider(SitemapSpider, StructuredDataSpider):
    name = "jets_pizza"
    item_attributes = {"brand": "Jet's Pizza", "brand_wikidata": "Q16997713", "name": "Jet's Pizza"}
    allowed_domains = ["www.jetspizza.com"]
    sitemap_urls = ["https://www.jetspizza.com/jp_store-sitemap.xml"]
    sitemap_rules = [(r"^https://www\.jetspizza\.com/stores/[^/]+/[^/]+/[^/]+/$", "parse_sd")]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        del item[
            "name"
        ]  # generic "Jet's Pizza <address> (<store code>)" on every page, backfilled from item_attributes
        item["ref"] = ld_data.get("identifier") or item["ref"]
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "pizza"
        yield item
