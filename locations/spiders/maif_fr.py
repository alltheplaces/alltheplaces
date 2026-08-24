import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider

# The generic national customer-service line, embedded in the structured
# data of "associations-collectivites-entreprises" agency pages rather than
# a branch-specific number. Compared digits-only since the raw phone
# string's formatting varies before PhoneCleanUpPipeline normalizes it.
NATIONAL_HOTLINE_DIGITS = "0978979899"


class MaifFRSpider(SitemapSpider, StructuredDataSpider):
    name = "maif_fr"
    item_attributes = {"brand": "Maif", "brand_wikidata": "Q3331029"}
    sitemap_urls = ["https://agence.maif.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"/details$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if re.sub(r"\D", "", item.get("phone") or "").endswith(NATIONAL_HOTLINE_DIGITS):
            item["phone"] = None
        yield item
