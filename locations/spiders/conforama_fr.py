from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ConforamaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "conforama_fr"
    item_attributes = {"brand": "Conforama", "brand_wikidata": "Q541134"}
    allowed_domains = ["www.conforama.fr"]
    sitemap_urls = ["https://www.conforama.fr/sitemap-magasins.xml"]
    sitemap_rules = [(r"/magasins-conforama/[\w-]+/[\w-]+$", "parse_sd")]
    # robots.txt disallows all UAs except a named crawler allowlist
    custom_settings = {"ROBOTSTXT_OBEY": False}
    # Cloudflare blocks cloud/datacenter ASNs regardless of User-Agent
    requires_proxy = True
    # National call centre number shared by almost every store, not a per-branch line.
    generic_phone = "+33 892 010 808"

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)  # Same generic brand image on every store page.
        if ld_data.get("telephone") == self.generic_phone:
            item["phone"] = None
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
