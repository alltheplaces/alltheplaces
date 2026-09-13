from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category
from locations.user_agents import FIREFOX_LATEST


class NocibeFRSpider(SitemapSpider, StructuredDataSpider):
    name = "nocibe_fr"
    item_attributes = {"brand": "Nocibé", "brand_wikidata": "Q3342592",}
    sitemap_urls = ["https://www.nocibe.fr/api/v2/fr_FR_ncb/sitemap/storesitemap0.xml"]
    sitemap_rules = [(r"/\d+$", "parse_sd")]
    custom_settings = {"USER_AGENT": FIREFOX_LATEST} #BROWSER_DEFAULT does not work
    wanted_types = ["LocalBusiness"]
    drop_attributes = ["facebook", "image"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name", "")
        apply_category(Categories.SHOP_PERFUMERY, item)
        yield item

