import json

import scrapy

from locations.hours import DAYS_EN, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class HarveyNormanSpider(StructuredDataSpider):
    name = "harvey_norman"
    item_attributes = {"brand": "Harvey Norman", "brand_wikidata": "Q4040441"}
    allowed_domains = ["stores.harveynorman.com.au", "stores.harveynorman.co.nz"]
    start_urls = ["https://stores.harveynorman.com.au/", "https://stores.harveynorman.co.nz/"]
    requires_proxy = "AU"

    def parse(self, response):
        data_raw = response.xpath('//script[@type="application/ld+json"]/text()').get()
        for store in json.loads(data_raw):
            yield scrapy.Request(url=store["url"], callback=self.parse_sd)

    def pre_process_data(self, ld_data, **kwargs):
        # openingHoursSpecification data exists but needs to first
        # be corrected prior to use.
        oh_spec = ld_data.pop("openingHoursSpecification")
        for day_range in oh_spec:
            day_range["opens"] = "".join(day_range["opens"].upper().split())
            if ":" not in day_range["opens"]:
                day_range["opens"] = day_range["opens"].replace("AM", ":00AM").replace("PM", ":00PM")
            day_range["closes"] = "".join(day_range["closes"].upper().split())
            if ":" not in day_range["closes"]:
                day_range["closes"] = day_range["closes"].replace("AM", ":00AM").replace("PM", ":00PM")
            if "dayOfWeek" in day_range:
                for day_name in day_range["dayOfWeek"]:
                    day_name = day_name.title()
        ld_data["openingHoursSpecification"] = oh_spec

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image")
        if "stores.harveynorman.com.au" in response.url:
            item["country"] = "AU"
        else:
            item["country"] = "NZ"
            item.pop("state")
        oh = OpeningHours()
        oh.from_linked_data(ld_data, time_format="%I:%M%p")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
