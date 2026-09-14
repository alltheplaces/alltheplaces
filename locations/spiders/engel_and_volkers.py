import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class EngelAndVolkersSpider(SitemapSpider, StructuredDataSpider):
    name = "engel_and_volkers"
    item_attributes = {"brand": "Engel & Völkers", "brand_wikidata": "Q1341765"}
    sitemap_urls = ["https://www.engelvoelkers.com/sitemap_shop_profile.xml"]
    sitemap_rules = [(r"/en/shops/[^/]+$", "parse_sd")]
    wanted_types = ["RealEstateAgent"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        next_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not next_data:
            return
        shop = json.loads(next_data).get("props", {}).get("pageProps", {}).get("shopData") or {}
        if shop.get("shopStatus") and shop["shopStatus"] != "OPENED":
            return

        if geo := shop.get("geoLocation"):
            item["lat"] = geo.get("lat")
            item["lon"] = geo.get("lng")

        item["ref"] = shop.get("masterDataShopId") or item.get("ref")
        item["website"] = response.url

        apply_category(Categories.OFFICE_ESTATE_AGENT, item)

        yield item
