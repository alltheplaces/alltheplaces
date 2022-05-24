# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class WHSmithUKSpider(scrapy.Spider):
    name = "whsmith_uk"
    item_attributes = {"brand": "WHSmith", "brand_wikidata": "Q1548712"}
    allowed_domains = ["whsmith.co.uk"]

    def start_requests(self):
        base_url = "https://www.whsmith.co.uk/stores/details?StoreID="

        ## Coulnd't find store ids anywhere so just loop through 4 digits
        for id in range(1000, 9999):
            if id == 4069:  ##internal server error
                pass
            else:
                url = base_url + str(id)
                yield scrapy.Request(url=url, callback=self.parse, meta={"id": id})

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for group in hours:
            if type(group["dayOfWeek"]) == list:
                for d in group["dayOfWeek"]:
                    day = DAY_MAPPING[d]
                    open_time = group["opens"]
                    close_time = group["closes"]

                    opening_hours.add_range(
                        day=day,
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H:%M",
                    )
            else:
                day = DAY_MAPPING[group["dayOfWeek"]]
                open_time = group["opens"]
                close_time = group["closes"]

                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        if response.xpath(
            'normalize-space(//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text())'
        ).extract_first():
            data = json.loads(
                response.xpath(
                    'normalize-space(//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text())'
                ).extract_first()
            )

            properties = {
                "ref": response.meta.get("id"),
                "name": data["@graph"][0]["name"],
                "addr_full": data["@graph"][1]["address"]["streetAddress"],
                "city": data["@graph"][1]["address"]["addressLocality"],
                "postcode": data["@graph"][1]["address"]["postalCode"],
                "country": data["@graph"][1]["address"]["addressCountry"],
                "lat": data["@graph"][1]["geo"]["latitude"],
                "lon": data["@graph"][1]["geo"]["longitude"],
                "phone": data["@graph"][1]["telephone"],
                "website": response.url,
            }

            hours = self.parse_hours(data["@graph"][1]["openingHoursSpecification"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)

        else:
            pass
