import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

SHARED_LOGOS = [
    "i_shop_workman",
    "i_shop_workmanplus",
    "i_shop_workmancolors",
    "plusshop.png",
    "plusshop-1200",
    "wp_tenpo-29",
]


class WorkmanJPSpider(SitemapSpider, StructuredDataSpider):
    name = "workman_jp"
    item_attributes = {"brand": "ワークマン", "brand_wikidata": "Q11351660"}
    sitemap_urls = ["https://www.workman.co.jp/store-sitemap.xml"]
    sitemap_rules = [(r"/store/[^/]+$", "parse_sd")]
    wanted_types = ["Store"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any):
        store_name = ld_data.get("name", "")

        # Determine brand from store name in JSON-LD
        if store_name.startswith("Workman Colors"):
            item["brand"] = "Workman Colors"
            item["brand_wikidata"] = "Q11351660"
            branch = store_name.removeprefix("Workman Colors").strip()
        elif "ワークマンプラス2" in store_name:
            item["brand"] = "ワークマンプラス2"
            item["brand_wikidata"] = "Q11351660"
            branch = re.sub(r"ワークマンプラス2\s*", "", store_name).strip()
        elif "ワークマンプラス" in store_name:
            item["brand"] = "ワークマンプラス"
            item["brand_wikidata"] = "Q11351660"
            branch = re.sub(r"ワークマンプラス\s*", "", store_name).strip()
        else:
            branch = re.sub(r"^ワークマン\s*", "", store_name).strip()

        item["branch"] = branch if branch else None
        item["name"] = None

        # Extract opening hours from the DL address block
        hours_text = (
            response.xpath(
                "//dl[contains(@class,'address')]//dt[contains(text(),'営業時間')]/following-sibling::dd[1]/text()"
            )
            .get("")
            .strip()
        )
        if hours_text:
            m = re.match(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})", hours_text)
            if m:
                oh = OpeningHours()
                for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
                    oh.add_range(day, m.group(1), m.group(2))
                item["opening_hours"] = oh

        # Remove shared brand logos/placeholder images
        if item.get("image") and any(kw in item["image"] for kw in SHARED_LOGOS):
            item["image"] = None

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
