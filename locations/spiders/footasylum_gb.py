from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class FootasylumGBSpider(SitemapSpider, StructuredDataSpider):
    name = "footasylum_gb"
    item_attributes = {"brand": "Footasylum", "brand_wikidata": "Q126913565"}
    sitemap_urls = [
        "https://www.footasylum.com/ArticlesSiteMap.xml",
    ]
    sitemap_rules = [
        ("https://www.footasylum.com/store-locator/[^/]+/", "parse_sd"),
    ]
    requires_proxy = True
    wanted_types = ["Store"]
    drop_attributes = {"facebook", "image", "twitter"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_SHOES, item)
        yield item
