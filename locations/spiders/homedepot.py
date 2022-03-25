# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem


class HomeDepotSpider(scrapy.Spider):
    name = "homedepot"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["www.homedepot.com"]
    start_urls = ("https://www.homedepot.com/l/storeDirectory",)
    download_delay = 0.2

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for day in (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ):
            day_open = store_hours[day]["open"].zfill(5)
            day_close = store_hours[day]["close"].zfill(5)

            hours = day_open + "-" + day_close

            if hours == "00:00-00:00":
                # They're closed on this day
                continue

            day_short = day.title()[:2]

            if not this_day_group:
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day_short
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
        day_groups.append(this_day_group)

        if not day_groups:
            return None

        if len(day_groups) == 1:
            opening_hours = day_groups[0]["hours"]
            if opening_hours == "07:00-07:00":
                opening_hours = "24/7"
        else:
            opening_hours = ""
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        urls = response.xpath('//a[@class="stateList__link"]/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        state_urls = response.xpath(
            '//section[1]/div[2]/ul/li[@class="storeList__item"]/a/@href'
        ).extract()
        for state_url in state_urls:
            yield scrapy.Request(response.urljoin(state_url), callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        script_content = response.xpath("/html/head/script[5]/text()").extract_first()
        coord_data = re.search(
            r'"coordinates":(.*?}),', script_content, flags=re.IGNORECASE | re.DOTALL
        ).group(1)
        coords = json.loads(coord_data)
        store_hours_data = re.search(
            r'"storeHours":(.*?),"distance"',
            script_content,
            flags=re.IGNORECASE | re.DOTALL,
        ).group(1)
        store_hours = json.loads(store_hours_data)

        properties = {
            "phone": response.xpath(
                '//span[@itemprop="telephone"]/text()'
            ).extract_first(),
            "website": response.request.url,
            "ref": ref,
            "name": response.xpath(
                '//h1[@class="storeDetailHeader__storeName change-store-inline"]/text()'
            ).extract_first(),
            "addr_full": response.xpath(
                '//span[@class="location__storeAddressLine--street"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '// span[ @ itemprop = "addressRegion"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '// span[ @ itemprop = "addressLocality"]/text()'
            ).extract_first(),
            "lon": float(coords.get("lng")),
            "lat": float(coords.get("lat")),
        }

        opening_hours = self.store_hours(store_hours)
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)
