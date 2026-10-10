from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BodyMinuteFRSpider(SitemapSpider, StructuredDataSpider):
    name = "body_minute_fr"
    item_attributes = {
        "brand": "Body Minute",
        "brand_wikidata": "Q104972220",
    }
    sitemap_urls = ["https://bodyminute.com/robots.txt"]
    allowed_domains = ["bodyminute.com"]
    sitemap_rules = [
        (r"/instituts/[^/]+/$", "parse"),
    ]

    search_for_image = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["name"].startswith("Institut beauté et épilation sans RDV à"):
            apply_category(Categories.SHOP_BEAUTY, item)
            item["branch"] = (item.pop("name", "") or "").removeprefix("Institut beauté et épilation sans RDV à ")
            yield item
