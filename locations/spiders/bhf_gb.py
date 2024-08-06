from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class BhfGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bhf_gb"
    item_attributes = {"brand": "British Heart Foundation", "brand_wikidata": "Q4970039"}
    sitemap_urls = ["https://www.bhf.org.uk/sitemap.xml"]
    sitemap_rules = [
        (r"/find-bhf-near-you/.+-bhf-shop", "parse_sd"),
        ("-home-store$", "parse_sd"),
        ("/find-bhf-near-you/.+-furniture-electrical-store", "parse_sd"),
    ]
    wanted_types = ["ClothingStore", "HomeGoodsStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        self.crawler.stats.inc_value("z/{}".format(ld_data["@type"]))
        if "-bhf-shop" in response.url:
            apply_category(Categories.SHOP_CHARITY, item)
        elif "-home-store" in response.url or "-furniture-electrical-store" in response.url:
            apply_category(Categories.SHOP_FURNITURE, item)

        extract_google_position(item, response)

        if "phone" in item and item["phone"] is not None and item["phone"].replace(" ", "").startswith("+443"):
            item.pop("phone", None)

        yield item
