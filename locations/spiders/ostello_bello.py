from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class OstelloBelloSpider(SitemapSpider, StructuredDataSpider):
    name = "ostello_bello"
    item_attributes = {"brand": "Ostello Bello", "brand_wikidata": "Q130537992"}
    sitemap_urls = ["https://ostellobello.com/en/hostel-sitemap.xml"]
    sitemap_rules = [(r"/en/hostel/[^/]+/$", "parse_sd")]
    wanted_types = ["Hostel"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        apply_category(Categories.TOURISM_HOSTEL, item)
        yield item
