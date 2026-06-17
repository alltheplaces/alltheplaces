import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class WaffleHouseUSSpider(SitemapSpider):
    name = "waffle_house_us"
    item_attributes = {"brand": "Waffle House", "brand_wikidata": "Q1701206"}
    sitemap_urls = ["https://locations.wafflehouse.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z0-9-]+-[a-z]{2}-(\d+)/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not (m := re.search(r"businessSchema = (\{.*?\})\s*//\s*Append", response.text, re.S)):
            return
        ld_text = re.sub(
            r'"openingHoursSpecification"\s*:\s*openingHoursSpecification',
            '"openingHoursSpecification": []',
            m.group(1),
        )
        ld_data = json.loads(ld_text)

        item: Feature = LinkedDataParser.parse_ld(ld_data)
        item["ref"] = response.url.rstrip("/").rsplit("-", 1)[-1]
        item["website"] = response.url
        item.pop("name", None)
        item.pop("image", None)

        item["opening_hours"] = self.parse_opening_hours(response)
        apply_category(Categories.RESTAURANT, item)

        yield item

    def parse_opening_hours(self, response: Response) -> OpeningHours | None:
        if not (oc_match := re.search(r"const openClosed = \[(.*?)\];", response.text, re.S)):
            return None
        if not (bho_match := re.search(r"const bho = JSON\.parse\(`(\[.*?\])`\)", response.text, re.S)):
            return None
        open_closed = re.findall(r"'(open|closed)'", oc_match.group(1))
        bho = json.loads(bho_match.group(1))
        oh = OpeningHours()
        for day, status, times in zip(DAYS, open_closed, bho):
            if status == "closed":
                oh.set_closed(day)
            elif times == ["0000", "0000"]:
                oh.add_range(day, "00:00", "23:59")
            else:
                oh.add_range(day, f"{times[0][:2]}:{times[0][2:]}", f"{times[-1][:2]}:{times[-1][2:]}")
        return oh
