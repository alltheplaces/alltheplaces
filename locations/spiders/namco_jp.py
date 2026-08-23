from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class NamcoJPSpider(SitemapSpider, StructuredDataSpider):
    name = "namco_jp"
    item_attributes = {"brand": "namco", "brand_wikidata": "Q111516144"}
    sitemap_urls = ["https://bandainamco-am.co.jp/sitemap_game_center.xml"]
    sitemap_rules = [(r"^https://bandainamco-am\.co\.jp/game_center/loc/([\w-]+)/$", "parse_sd")]
    wanted_types = ["EntertainmentBusiness"]

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        # "PublicHolidays" is not a real day of the week and blows up
        # OpeningHours.add_range() for the whole item if left in, so
        # discard any rule that specifies it.
        if spec := ld_data.get("openingHoursSpecification"):
            if isinstance(spec, list):
                ld_data["openingHoursSpecification"] = [
                    rule
                    for rule in spec
                    if isinstance(rule, dict) and "publicholidays" not in str(rule.get("dayOfWeek", "")).lower()
                ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # This site also lists sibling brands (VS PARK, Tondemi, AZ PARK,
        # in-store "game corners" under other retailers' names, etc). Only
        # keep locations branded as "namco".
        if not (item["name"] or "").lower().startswith("namco"):
            return

        apply_category(Categories.AMUSEMENT_ARCADE, item)

        yield item
