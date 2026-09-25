from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category


class BodyMinuteFRSpider(SitemapSpider, StructuredDataSpider):
    name = "body_minute_fr"
    item_attributes = {
        "brand": "Body Minute",
        "brand_wikidata": "Q104972220",
    }
    sitemap_urls = ["https://bodyminute.com/robots.txt"]
    sitemap_rules = [
        (r"/instituts/[^/]+/$", "parse"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["name"].startswith("Institut beauté et épilation sans RDV à"):
            apply_category(Categories.SHOP_BEAUTY, item)
            item["branch"] = (item.pop("name","") or "").removeprefix("Institut beauté et épilation sans RDV à ")
            item["image"] = None
            yield item
