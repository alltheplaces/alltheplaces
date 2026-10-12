from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, sanitise_day
from locations.structured_data_spider import StructuredDataSpider


class MarcOrianSpider(SitemapSpider, StructuredDataSpider):
    name = "marc_orian"
    item_attributes = {"brand": "Marc Orian", "brand_wikidata": "Q99848767", "name": "Marc Orian"}
    sitemap_urls = ["https://www.marc-orian.com/sitemap_index.xml"]
    sitemap_follow = ["stores"]
    sitemap_rules = [(r"/details/magasin/\?storeID=(\w+)", "parse_sd")]
    wanted_types = ["JewelryStore"]
    search_for_image = False
    search_for_payment_accepted = False

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        # JSON-LD days are one day ahead of the hours shown on the page
        for rule in ld_data.get("openingHoursSpecification") or []:
            if day := sanitise_day(rule.get("dayOfWeek")):
                rule["dayOfWeek"] = DAYS[DAYS.index(day) - 1]
        ld_data.pop("image", None)

    def post_process_item(self, item, response, ld_data, **kwargs):
        branch = item.pop("name").removeprefix("Marc Orian - ").removeprefix("Marc Orian ")
        if branch != "null":
            item["branch"] = branch
        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
