from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TmobileUSSpider(SitemapSpider, StructuredDataSpider):
    name = "tmobile_us"
    item_attributes = {
        "brand": "T-Mobile",
        "brand_wikidata": "Q3511885",
    }
    sitemap_urls = ["https://www.t-mobile.com/stores/sitemap-business-main-pages.xml"]
    sitemap_rules = [(r"/stores/[a-z]{2}/t-mobile-", "parse_sd")]
    allowed_domains = ["www.t-mobile.com"]
    drop_attributes = {"facebook", "twitter"}

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data["openingHours"] = ld_data.pop("openingHoursSpecification", None)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["addr_full"] = item.pop("street_address", None)
        item["image"] = (
            ld_data["image"].split("(webp)")[1].strip("/") if "(webp)" in ld_data["image"] else ld_data["image"]
        )
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
