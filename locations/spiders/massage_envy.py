import re
from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MassageEnvySpider(SitemapSpider):
    name = "massage_envy"
    item_attributes = {"brand": "Massage Envy", "brand_wikidata": "Q10327170"}
    allowed_domains = ["locations.massageenvy.com"]
    sitemap_urls = ("https://locations.massageenvy.com/sitemap.xml",)
    sitemap_rules = [
        (r"^https://locations.massageenvy.com/[^/]+/[^/]+/[^/]+.html$", "parse"),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script_text = response.xpath('//*[contains(text(),"application/ld+json")]/text()').get()
        raw_data = chompjs.parse_js_object(
            re.search(r"structuredDataTextReview\s*\+=\s*`([^`]*)`", script_text).group(1) + "}"
        )
        item = DictParser.parse(raw_data)
        item["ref"] = response.url
        oh = OpeningHours()
        for day_time in raw_data["openingHoursSpecification"]:
            day = day_time["dayOfWeek"][0]
            open_time = day_time["opens"]
            close_time = day_time["closes"]
            oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        yield item
