from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider, clean_facebook


class ZadigEtVoltaireSpider(SitemapSpider, StructuredDataSpider):
    name = "zadig_et_voltaire"
    item_attributes = {
        "brand": "Zadig & Voltaire",
        "brand_wikidata": "Q3574548",
    }
    sitemap_urls = ["https://storelocator.zadig-et-voltaire.com/us/sitemap.xml"]
    sitemap_rules = [
        (r"/us/.*[0-9]+$", "parse_sd"),
    ]
    drop_attributes = ["twitter"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_CLOTHES, item)
        item["branch"] = (
            item.pop("name", "").removeprefix("Zadig&Voltaire ").removeprefix("Zadig & Voltaire ").removeprefix("- ")
        )

        if clean_facebook(item.get("facebook")) == "https://www.facebook.com/zadigvoltaire":
            item["facebook"] = None

        yield item
