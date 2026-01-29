from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

from locations.hours import sanitise_day, DAYS


class HistoireDorFRSpider(SitemapSpider, StructuredDataSpider):
    name = "histoire_dor_fr"
    item_attributes = {"brand": "Histoire d'Or", "brand_wikidata": "Q62529245"}
    sitemap_urls = ["https://www.histoiredor.com/sitemap_index.xml"]
    sitemap_follow = ["stores"]
    sitemap_rules = [("/details/magasin/", "parse_sd")]
    wanted_types = ["JewelryStore"]

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        for rule in ld_data.get("openingHoursSpecification") or []:
            if day := sanitise_day(rule.get("dayOfWeek")):
                rule["dayOfWeek"] = DAYS[DAYS.index(day) - 1]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("Histoire dʼOr - ", "")
        item.pop("image")
        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
