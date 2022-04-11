# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class TimHortonsSpider(scrapy.Spider):
    name = "timhortons"
    item_attributes = {"brand": "Tim Horton's", "brand_wikidata": "Q175106"}
    allowed_domains = ["locations.timhortons.com", "locations.timhortons.ca"]
    start_urls = (
        "https://locations.timhortons.com/sitemap.xml",
        "https://locations.timhortons.ca/sitemap.xml",
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//url/loc/text()").extract():
            if ".ca/fr/" in url:
                continue
            if url.count("/") != 5:
                continue
            yield scrapy.Request(url, callback=self.parse_location)

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
                        f_time[0:2], f_time[2:4], t_time[0:2], t_time[2:4]
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

    def parse_location(self, response):
        address = response.xpath('//*[@itemprop="address"]')[0]
        properties = {
            "lon": response.xpath('//*[@itemprop="longitude"]/@content').get(),
            "lat": response.xpath('//*[@itemprop="latitude"]/@content').get(),
            "addr_full": address.xpath(
                './/*[@itemprop="streetAddress"]/@content'
            ).get(),
            "city": address.css(".Address-city::text").get(),
            "state": address.xpath('.//*[@itemprop="addressRegion"]/text()').get(),
            "postcode": address.xpath('.//*[@itemprop="postalCode"]/text()').get(),
            "phone": response.xpath('//*[@itemprop="telephone"]/text()').get(),
            "name": response.xpath('//*[@class="LocationName-geo"]/text()').get(),
            "ref": response.url,
            "website": response.url,
        }

        hours_elem = response.xpath(
            '//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days'
        )
        opening_hours = None
        if hours_elem:
            hours = json.loads(hours_elem.extract_first())
            opening_hours = self.store_hours(hours)

        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)
