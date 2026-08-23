from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BenuCZSpider(SitemapSpider, StructuredDataSpider):
    name = "benu_cz"
    item_attributes = {"brand": "BENU", "brand_wikidata": "Q58170509"}
    requires_proxy = True
    # Pharmacy pages do not follow a consistent URL pattern, so crawl the
    # entire page sitemap and rely on StructuredDataSpider filtering by
    # wanted_types to pick out only the pharmacy pages.
    sitemap_urls = [
        "https://www.benu.cz/sitemap_page_001.xml",
        "https://www.benu.cz/sitemap_fresh_page_001.xml",
    ]
    sitemap_rules = [(r"", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Parcel pickup boxes/lockers and pure e-shop collection points share
        # the same LocalBusiness structured data as full pharmacies but are
        # not pharmacies themselves, so skip them.
        if "vydejni-box" in response.url or "e-shop" in response.url:
            return

        item["country"] = "CZ"
        # This is a generic national customer-service line embedded in every
        # page's structured data, not a branch-specific number.
        if item.get("phone") == "+420 212 812 811":
            item["phone"] = None
        apply_category(Categories.PHARMACY, item)
        yield item
