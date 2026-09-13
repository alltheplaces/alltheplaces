import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class TearJPSpider(SitemapSpider, StructuredDataSpider):
    name = "tear_jp"
    item_attributes = {"brand": "ティア", "brand_wikidata": "Q11318901"}
    sitemap_urls = ["https://www.tear.co.jp/sitemap/hall.detail.xml"]
    sitemap_rules = [(r"/hall/\d+$", "parse_sd")]

    # A generic group-wide call centre number ("0120-549453", sometimes
    # annotated "（ティアにつながります）" i.e. "connects to Tear") is used
    # by around 60% of halls in place of a real direct line, so it's
    # dropped rather than reported as branch-specific contact info.
    GENERIC_PHONE_DIGITS = "0120549453"

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("phone"):
            item["phone"] = re.sub(r"[（(].*[）)]\s*$", "", item["phone"]).strip()
            if re.sub(r"\D", "", item["phone"]) == self.GENERIC_PHONE_DIGITS:
                item["phone"] = None

        if "noimage" in (item.get("image") or ""):
            item["image"] = None

        apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)

        yield item
