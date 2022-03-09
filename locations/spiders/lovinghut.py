# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class LovinghutSpider(scrapy.Spider):
    name = "lovinghut"
    item_attributes = {"brand": "Loving Hut"}
    allowed_domains = ["lovinghut.us"]
    start_urls = ("http://lovinghut.us/locations",)

    def normalize_time(self, time_str):
        match = re.search(
            "(.*) (am|a.m|pm|noon|p.m) \u2013 (.*) (am|a.m||pm|noon|p.m)", time_str
        )
        h1, am_pm1, h2, am_pm2 = match.groups()
        h1 = h1.split(":")
        h2 = h2.split(":")

        return "%02d:%02d-%02d:%02d" % (
            int(h1[0]) + 12
            if am_pm1 == "pm" or am_pm1 == "noon" or am_pm1 == "p.m"
            else int(h1[0]),
            int(h1[1]) if len(h1) > 1 else 0,
            int(h2[0]) + 12
            if am_pm2 == "pm" or am_pm2 == "noon" or am_pm2 == "p.m"
            else int(h2[0]),
            int(h2[1]) if len(h2) > 1 else 0,
        )

    def parse(self, response):
        stores = response.xpath('//td[@class="tg-citi"]')
        full_addresses = response.xpath('//td[@class="tg-addr"]/text()').extract()
        phones = response.xpath(
            '//tr[contains(@style, "padding-bottom:10px")]/td[1]//a//text()'
        ).extract()
        index = 0
        for store in stores:
            store_url = store.xpath("a/@href")[0].extract()

            address_match = re.search(r"(.*)\,\s(.*?)$", full_addresses[index])
            address_full, city_state = address_match.groups()
            match = re.search(r"([\w\s]+)\s(\w+)\s(\w+)", city_state)
            city, state, postcode = match.groups()

            props = {
                "website": store_url,
                "addr_full": address_full,
                "city": city,
                "state": state,
                "postcode": postcode,
                "phone": phones[index],
                "ref": city + ", " + state,
            }

            index += 1

            yield scrapy.Request(
                store_url, meta={"product": props}, callback=self.parse_detail_product
            )

    def parse_detail_product(self, response):
        tr_days = response.xpath('//table[@class="hours"]//tr')
        product = response.meta.get("product")
        opening_hours = ""
        index = 0

        for tr_day in tr_days:
            open_hours = tr_day.xpath("td//h4/text()").extract()

            if len(open_hours) == 0:
                open_hours = tr_day.xpath("td//strong/text()").extract()

            if len(open_hours) == 0:
                open_hours = tr_day.xpath("td//text()").extract()

            if len(open_hours) == 2:
                day = open_hours[0]
                hours = open_hours[1]

                if day == "Last Order":
                    continue

                if hours.lower().find("closed") == -1:
                    open_days = day.split(" \u2013 ")
                    if len(open_days) == 2:
                        opening_hours += (
                            ("; " if index > 0 else "")
                            + open_days[0][:2]
                            + "-"
                            + open_days[1][:2]
                            + " "
                            + self._clean_text(self.normalize_time(hours))
                        )
                    elif len(open_days) == 1:
                        opening_hours += (
                            ("; " if index > 0 else "")
                            + open_days[0][:2]
                            + " "
                            + self._clean_text(self.normalize_time(hours))
                        )
                index += 1
            elif len(open_hours) == 1:
                hours = open_hours[0]
                opening_hours += " " + self.normalize_time(hours)

        product["opening_hours"] = opening_hours

        yield GeojsonPointItem(**product)

    def _clean_text(self, text):
        return re.sub("[\r\n\t]", "", text).strip()
