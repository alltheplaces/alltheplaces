# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class FazolisSpider(scrapy.Spider):

    name = "fazolis"
    item_attributes = {"brand": "Fazoli's", "brand_wikidata": "Q1399195"}
    allowed_domains = ["locations.fazolis.com"]
    start_urls = ("https://locations.fazolis.com/",)

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for day_info in store_hours:
            day = day_info["day"][:2].title()

            hour_intervals = []
            for interval in day_info["intervals"]:
                f_time = str(interval["start"]).zfill(4)
                t_time = str(interval["end"]).zfill(4)
                hour_intervals.append(
                    "{}:{}-{}:{}".format(
                        f_time[0:2],
                        f_time[2:4],
                        t_time[0:2],
                        t_time[2:4],
                    )
                )
            hours = ",".join(hour_intervals)

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

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
                elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def store_info(self, store):
        address = store.xpath(
            '//meta[contains(@itemprop,"streetAddress")]/@content'
        ).extract_first()
        city = store.xpath(
            '//span[contains(@itemprop,"addressLocality")]/text()'
        ).extract_first()
        state = store.xpath(
            '//abbr[contains(@itemprop,"addressRegion")]/text()'
        ).extract_first()
        zip_code = store.xpath(
            '//span[contains(@itemprop,"postalCode")]/text()'
        ).extract_first()
        hours = json.loads(
            store.xpath(
                '//div[@class="location-info-col-split right-split"]//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days'
            ).extract_first()
        )
        props = {
            "addr_full": address,
            "city": city,
            "state": state,
            "postcode": zip_code,
            "phone": store.xpath(
                '//span[contains(@itemprop,"telephone")]/text()'
            ).extract_first(),
            "ref": store.url,
            "name": store.xpath(
                'string(//h1[contains(@itemprop,"name")])'
            ).extract_first(),
            "website": store.url,
            "lat": float(
                store.xpath(
                    '//meta[contains(@itemprop,"latitude")]/@content'
                ).extract_first()
            ),
            "lon": float(
                store.xpath(
                    '//meta[contains(@itemprop,"longitude")]/@content'
                ).extract_first()
            ),
        }
        if hours:
            props["opening_hours"] = self.store_hours(hours)

        return GeojsonPointItem(**props)

    def parse_store(self, store):
        yield self.store_info(store)

    # Once per city, parse stores
    def parse_city(self, city):
        # Some times >1 store per city.
        city_stores = city.xpath(
            '//ul[@class="c-LocationGridList"]/li//a[@class="Teaser-titleLink"]/@href'
        ).extract()
        if len(city_stores) > 0:
            for store in city_stores:
                yield scrapy.Request(city.urljoin(store), callback=self.parse_store)
        # Single store in a city means store info is in this page
        else:
            yield self.store_info(city)

    # Once per state, gets cities.
    def parse_state(self, state):
        cities = state.xpath(
            '//ul[@class="c-directory-list-content"]/li/a/@href'
        ).extract()
        state_stores = state.xpath(
            '//ul[@class="c-LocationGridList"]/li//a[@class="Teaser-titleLink"]/@href'
        ).extract()
        # Check for city listings first:
        if len(cities) > 0:
            for city in cities:
                yield scrapy.Request(state.urljoin(city), callback=self.parse_city)
        # Single city has multiple stores:
        elif len(state_stores) > 0:
            for store in state_stores:
                yield scrapy.Request(state.urljoin(store), callback=self.parse_store)
        # Single store in a state means store info is in this page:
        else:
            yield self.store_info(state)

    # Initial request, gets states.
    def parse(self, response):
        states = response.xpath(
            '//ul[@class="c-directory-list-content"]/li/a/@href'
        ).extract()
        for state in states:
            yield scrapy.Request(response.urljoin(state), callback=self.parse_state)
