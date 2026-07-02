import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class FarmersInsuranceUSSpider(SitemapSpider, StructuredDataSpider):
    name = "farmers_insurance_us"
    item_attributes = {"brand": "Farmers Insurance", "brand_wikidata": "Q1396863"}
    allowed_domains = ["agents.farmers.com"]
    sitemap_urls = ["https://agents.farmers.com/sitemap.xml"]
    sitemap_rules = [(r"https://agents\.farmers\.com/\w{2}/[-\w]+/[-\w]+/?$", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = re.search(r"\{.*\}", response.xpath('//comment()[contains(., "LocalBusiness")]').get(), re.S).group(0)
        item = DictParser.parse(json.loads(data))
        item["ref"] = item["website"] = response.url
        try:
            oh = OpeningHours()
            for day_time in json.loads(data)["openingHoursSpecification"]:
                day = day_time["dayOfWeek"][0]
                open_time = day_time["opens"]
                close_time = day_time["closes"]
                oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh
        except:
            pass
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
