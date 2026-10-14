import html
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class PenskeSpider(SitemapSpider, StructuredDataSpider):
    name = "penske"
    item_attributes = {"brand_wikidata": "Q81234570"}
    allowed_domains = ["pensketruckrental.com"]
    sitemap_urls = ["https://www.pensketruckrental.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/us/[-\w]+/[-\w]+/[0-9]+/$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"email", "image"}

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        if isinstance(ld_data.get("openingHours"), list):
            ld_data["openingHours"] = [self.clean_hours_rule(rule) for rule in ld_data["openingHours"]]

    @staticmethod
    def clean_hours_rule(rule: str) -> str:
        # Times are mostly 24-hour with a stray AM/PM suffix; "00:00 AM - 00:00 PM" means closed
        if m := re.fullmatch(r"(\S+) (\d+):(\d+) ([AP])M - (\d+):(\d+) ([AP])M", rule.strip()):
            days, open_h, open_m, open_meridiem, close_h, close_m, close_meridiem = m.groups()
            if int(open_h) == int(open_m) == int(close_h) == int(close_m) == 0:
                return f"{days} closed"
            if open_meridiem == "P" and 0 < int(open_h) < 12:
                open_h = str(int(open_h) + 12)
            if close_meridiem == "P" and 0 < int(close_h) < 12:
                close_h = str(int(close_h) + 12)
            return f"{days} {open_h}:{open_m}-{close_h}:{close_m}"
        return rule

    def post_process_item(self, item, response, ld_data):
        item["ref"] = re.findall("[0-9]+", response.url)[0]
        item["branch"] = html.unescape(item.pop("name"))
        apply_category(Categories.SHOP_RENTAL, item)
        yield item
