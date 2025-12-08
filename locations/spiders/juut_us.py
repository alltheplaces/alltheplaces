from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class JuutUSSpider(SitemapSpider, StructuredDataSpider):
    name = "juut_us"
    item_attributes = {"brand": "Juut"}
    sitemap_urls = ["https://juut.com/locations-sitemap.xml"]
    sitemap_rules = [
        (r"https://juut.com/locations/[\w-]+/", "parse"),
    ]
    wanted_types = ["BeautySalon"]
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("JUUT ")
        apply_category(Categories.SHOP_HAIRDRESSER, item)
        yield item
