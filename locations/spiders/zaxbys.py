# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

DAYS = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Friday": "Fr",
    "Thursday": "Th",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class ZaxbysSpider(scrapy.Spider):
    name = "zaxbys"
    item_attributes = {"brand": "Zaxby's", "brand_wikidata": "Q8067525"}
    allowed_domains = ["zaxbys.com"]
    start_urls = ("https://www.zaxbys.com/locations",)

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for line in store_hours:
            day = line["dayOfWeek"][0][:2]

            if not line["opens"]:
                continue

            hours = line["opens"] + "-" + line["closes"]

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

        if this_day_group:
            day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                elif day_group["from_day"] == "Mo" and day_group["to_day"] == "Su":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def phone_normalize(self, phone):
        r = re.search(
            r"\+?(\s+)*(\d{1})?(\s|\()*(\d{3})(\s+|\)|-)*(\d{3})(\s+|-)?(\d{2})(\s+|-)?(\d{2})",
            phone,
        )
        return (
            (
                "("
                + r.group(4)
                + ") "
                + r.group(6)
                + "-"
                + r.group(8)
                + "-"
                + r.group(10)
            )
            if r
            else phone
        )

    def parse(self, response):  # high-level list of states
        states = response.xpath('//map/area[@shape="poly"]/@href').extract()
        for path in states:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_states)

    def parse_states(self, response):
        if response.xpath('//script[contains(.,"var locations")]'):
            stores = json.loads(
                re.search(
                    r"var locations =(.*);",
                    response.xpath(
                        '//script[contains(.,"var locations")]'
                    ).extract_first(),
                )[1]
            )
        else:
            stores = []
        for store in stores:
            yield scrapy.Request(
                response.urljoin(store["Website"]), callback=self.parse_store
            )

    def parse_store(self, response):
        try:
            data = json.loads(
                re.search(
                    r'(.*)"acceptsReservations.*',
                    response.xpath('//script[@type="application/ld+json"]/text()')
                    .extract_first()
                    .replace("\r\n", ""),
                )[1]
            )
        except Exception as e:

            yield scrapy.Request(response.url, callback=self.parse_store)
            return

        yield GeojsonPointItem(
            lat=float(data["geo"]["latitude"]),
            lon=float(data["geo"]["longitude"]),
            phone=self.phone_normalize(data["telephone"]),
            website=data["url"],
            ref=data["url"],
            opening_hours=self.store_hours(data["openingHoursSpecification"]),
            addr_full=data["address"]["streetAddress"],
            city=data["address"]["addressLocality"],
            state=data["address"]["addressRegion"],
            postcode=data["address"]["postalCode"],
            country="US",
        )
