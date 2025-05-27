from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KpnNLSpider(SitemapSpider, StructuredDataSpider):
    name = "kpn_nl"
    item_attributes = {"brand": "KPN", "brand_wikidata": "Q338633"}
    sitemap_urls = ["https://www.kpn.com/nr/sitemap_stores.xml"]
    sitemap_rules = [(r"kpn\.com/winkel/[-\w]+/[-\w]+$", "parse_sd")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        hours = []
        for rule in ld_data.get("openingHours", []):
            hours.append(rule.replace("null - null", "closed"))
        ld_data["openingHours"] = hours

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
