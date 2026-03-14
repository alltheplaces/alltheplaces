from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AtolSpider(SitemapSpider, StructuredDataSpider):
    name = "atol"
    item_attributes = {"brand": "Atol", "brand_wikidata": "Q2869542"}
    sitemap_urls = ["https://magasins.atol.fr/sitemap.xml"]
    sitemap_rules = [
        ("/france/", "parse_sd"),
        ("/guyane-francaise/", "parse_sd"),
        ("/martinique/", "parse_sd"),
        ("/guadeloupe/", "parse_sd"),
        ("/nouvelle-caledonie/", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "Audition" in item.get("name"):
            apply_category(Categories.SHOP_HEARING_AIDS, item)
        else:
            apply_category(Categories.SHOP_OPTICIAN, item)
        yield item
