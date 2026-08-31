import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class FarmersInsuranceUSSpider(SitemapSpider):
    name = "farmers_insurance_us"
    item_attributes = {"brand": "Farmers Insurance", "brand_wikidata": "Q1396863"}
    allowed_domains = ["agents.farmers.com"]
    sitemap_urls = ["https://agents.farmers.com/sitemap.xml"]
    sitemap_rules = [(r"https://agents\.farmers\.com/\w{2}/[-\w]+/[-\w]+/?$", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        comment = response.xpath('//comment()[contains(., "LocalBusiness")]').get()
        if not comment:
            return
        match = re.search(r"\{.*\}", comment, re.S)
        if not match:
            return
        data = json.loads(match.group(0))
        item = DictParser.parse(data)
        item["ref"] = item["website"] = response.url
        try:
            oh = OpeningHours()
            for day_time in data.get("openingHoursSpecification", []):
                days = day_time.get("dayOfWeek", [])
                if not days:
                    continue
                oh.add_range(days[0], day_time.get("opens"), day_time.get("closes"))
            if oh:
                item["opening_hours"] = oh
        except (KeyError, IndexError, ValueError, TypeError):
            pass
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
