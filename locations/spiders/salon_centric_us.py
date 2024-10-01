from scrapy.spiders import SitemapSpider

from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider


class SalonCentricUSSpider(SitemapSpider, StructuredDataSpider):
    name = "salon_centric_us"
    item_attributes = {
        "brand": "SalonCentric",
        "brand_wikidata": "Q124339481",
        "extras": {"shop": "hairdresser_supply"},
    }
    sitemap_urls = ["https://stores.saloncentric.com/sitemap.xml"]
    sitemap_rules = [(r"com/\w\w/[^/]+/(\d+)$", "parse")]
    wanted_types = ["HealthAndBeautyBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "Coming Soon" in item["name"]:
            return
        item["branch"] = item.pop("name").removeprefix("SalonCentric").strip(" -")

        if "closed " in item["branch"].lower():
            set_closed(item)

        yield item
    drop_attributes = {"image"}
