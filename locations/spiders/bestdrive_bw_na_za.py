from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class BestdriveBWNAZASpider(SitemapSpider, StructuredDataSpider):
    name = "bestdrive_bw_na_za"
    item_attributes = {"brand": "BestDrive", "brand_wikidata": "Q63057183", "extras": Categories.SHOP_CAR_REPAIR.value}
    sitemap_urls = ["https://www.bestdrive.co.za/robots.txt"]
    sitemap_rules = [(r"https://www.bestdrive.co.za/fitment-centre/.*", "parse")]
    wanted_types = ["TireShop"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        if "BestDriveSouthAfrica" in item.get("facebook"):
            item.pop("facebook")
        yield item
