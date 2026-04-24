from scrapy.spiders import SitemapSpider

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
from locations.structured_data_spider import StructuredDataSpider


class AesopSpider(SitemapSpider, StructuredDataSpider, CamoufoxSpider):
    name = "aesop"
    item_attributes = {"brand": "Aesop", "brand_wikidata": "Q4688560"}
    allowed_domains = ["www.aesop.com"]
    sitemap_urls = ["https://www.aesop.com/sitemap_index.xml"]
    sitemap_rules = [(r"/[a-z]{2}/stores?/[^/]+/?$", "parse_sd")]
    wanted_types = ["LocalBusiness", "Store", "HealthAndBeautyBusiness"]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        if name := item.pop("name", None):
            item["branch"] = name.replace("Aesop ", "")
        item["website"] = response.url
        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
