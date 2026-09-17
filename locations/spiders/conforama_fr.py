from typing import Iterable

from scrapy import Selector
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
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
    wanted_types = ["FurnitureStore"]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if (item.get("name") or "").startswith("Conforama "):
            item["branch"] = item.pop("name").removeprefix("Conforama ")
        item.pop("image", None)  # Same generic brand image on every store page.
        if ld_data.get("telephone") == self.generic_phone:
            item["phone"] = None
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item

    def extract_payment_accepted(self, item: Feature | dict, selector: Selector, ld_item: dict) -> None:
        if isinstance(ld_item.get("paymentAccepted"), str):
            methods = ld_item["paymentAccepted"].split(", ")
            apply_yes_no(PaymentMethods.CASH, item, "cash" in methods)
            apply_yes_no(PaymentMethods.CARDS, item, "carte bancaire" in methods)
            apply_yes_no(PaymentMethods.GIFT_CARD, item, "carte cadeau" in methods)
