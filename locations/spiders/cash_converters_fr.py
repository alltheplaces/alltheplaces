from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CashConvertersFRSpider(SitemapSpider, StructuredDataSpider):
    name = "cash_converters_fr"
    item_attributes = {
        "brand": "Cash Converters",
        "brand_wikidata": "Q124606631",
    }
    sitemap_urls = ["https://magasins.cashconverters.fr/sitemap.xml"]
    sitemap_rules = [
        (r"-[0-9]+", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):

        apply_category(Categories.SHOP_PAWNBROKER, item)
        name = item.pop("name", "")
        if "carrefour" not in name.lower():
            item["branch"] = name.removeprefix("Cash Converters ")
            item["website"] = (item.get("website") or "").replace("//www.", "//magasins.")
            yield item
