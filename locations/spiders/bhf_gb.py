from scrapy.spiders import SitemapSpider
from scrapy.http import Request

from locations.items import Feature
from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class BhfGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bhf_gb"
    item_attributes = {"brand": "British Heart Foundation", "brand_wikidata": "Q4970039"}
    sitemap_urls = ["https://www.bhf.org.uk/sitemap.xml"]
    sitemap_rules = [
#        (r"/find-bhf-near-you/.+-shop$", "parse_sd"),
#        (r"/find-bhf-near-you/.+-store$", "parse_sd"),
        (r"/find-bhf-near-you/.+-shop$", "parse"),
        (r"/find-bhf-near-you/.+-store$", "parse"),
    ]
    wanted_types = ["ClothingStore", "HomeGoodsStore"]
    drop_attributes = {"image"}

    search_for_twitter = False
    search_for_facebook = False

    def parse(self, response):
        if "ld+json" in response.text:
            for item in self.parse_sd(response):
                extract_google_position(item, response)
                if "phone" in item and item["phone"] is not None and item["phone"].replace(" ", "").startswith("+443"):
                    item.pop("phone", None)
                item["branch"] = item.pop("name")
        else:
            item = Feature()
            item["ref"] = response.url
            item["name"] = 'British Heart Foundation'
            item["branch"] = response.xpath('//h1/text()').get()
        if "-bhf-shop" in response.url:
            apply_category(Categories.SHOP_CHARITY, item)
        elif "-home-store" in response.url or "-furniture-electrical-store" in response.url:
            apply_category(Categories.SHOP_FURNITURE, item)
        else:
            apply_category(Categories.SHOP_CHARITY, item)
        yield item
