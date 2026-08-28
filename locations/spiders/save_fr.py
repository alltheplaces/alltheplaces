from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class SaveFRSpider(SitemapSpider, StructuredDataSpider):
    name = "save_fr"
    item_attributes = {
        "brand": "Save",
        "brand_wikidata": "Q121289450",
        "extras": Categories.SHOP_MOBILE_PHONE.value,
    }
    sitemap_urls = ["https://magasin.save.co/sitemap.xml"]
    sitemap_rules = [(r"https://magasin\.save\.co/.+\d+/?$", "parse_sd")]
    wanted_types = ["MobilePhoneStore"]
    drop_attributes = {"image"}
