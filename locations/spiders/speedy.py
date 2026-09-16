import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SpeedySpider(SitemapSpider, StructuredDataSpider):
    name = "speedy"
    item_attributes = {"brand": "Speedy", "brand_wikidata": "Q3492969", "name": "Speedy"}
    allowed_domains = ["centres-auto.speedy.fr"]
    sitemap_urls = ["https://centres-auto.speedy.fr/sitemap.xml"]
    sitemap_rules = [(r"^https://centres-auto\.speedy\.fr/garage/[^/]+/\d+$", "parse")]
    # The site struggles under the default concurrency, causing many requests to time out
    # and be retried; a lower per-domain concurrency is more reliable and faster overall.
    custom_settings = {"CONCURRENT_REQUESTS_PER_DOMAIN": 2}
    # As well as mainland France and French overseas departments/territories (each with
    # their own ISO country code), this store finder also lists some branches in Morocco.
    # There's no country field in the source data, so let the reverse geocoding fallback
    # determine the correct country per item rather than guessing from the domain/name.
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        if not item.get("lat") or not item.get("lon"):
            # A review widget on the page also carries LocalBusiness microdata, but with
            # no coordinates or opening hours, so skip it.
            return
        item["branch"] = re.sub(r"^Centre Auto Speedy ", "", item.pop("name"), flags=re.IGNORECASE)
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
