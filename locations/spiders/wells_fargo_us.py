import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class WellsFargoUSSpider(SitemapSpider):
    name = "wells_fargo_us"
    item_attributes = {"brand": "Wells Fargo", "brand_wikidata": "Q744149"}
    sitemap_urls = ["https://locations.wellsfargo.com/sitemap.xml"]
    sitemap_rules = [("https://locations.wellsfargo.com/(?!es)[^/]+/[^/]+/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(response.xpath('//*[@type="application/ld+json"]/text()').get())["credentialSubject"]
        item = DictParser.parse(raw_data)
        item["name"] = item["name"].replace("Bank", "").replace("ATM", "")
        item["ref"] = item["website"] = response.url
        oh = OpeningHours()
        if opening_hours_data := raw_data.get("openingHoursSpecification"):
            for day_time in opening_hours_data:
                if day := day_time.get("dayOfWeek", ""):
                    day = day.replace("https://schema.org/", "")
                    open_time = day_time.get("opens")
                    close_time = day_time.get("closes")
                    if open_time:
                        oh.add_range(day, open_time, close_time)
        item["opening_hours"] = oh
        title_text = response.xpath("//title/text()").get().strip()
        if "Branch with ATM" in title_text:
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, True)
        elif "Fargo ATM" in title_text:
            apply_category(Categories.ATM, item)
        elif "Fargo Branch at" in title_text:
            apply_category(Categories.BANK, item)
        yield item
