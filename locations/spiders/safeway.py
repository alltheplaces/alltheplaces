# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class SafewaySpider(scrapy.Spider):
    name = "safeway"
    item_attributes = {"brand": "Safeway", "brand_wikidata": "Q1508234"}
    allowed_domains = ["safeway.com"]
    start_urls = ("https://local.safeway.com/sitemap.xml",)

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

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//*/*[@href]").extract()
        for path in city_urls:
            locationURL = re.compile(
                r"https://local.safeway.com/(safeway/|\S+)/\S+/\S+/\S+.html"
            )
            if not re.search(locationURL, path):
                pass
            else:
                path = re.search(locationURL, path)[0].strip('"/>')
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):
        properties = {
            "name": response.xpath('//meta[@itemprop="name"]/@content').extract_first(),
            "website": response.url,
            "ref": response.url,
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@itemprop="addressLocality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()')
            .extract_first()
            .strip(),
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "extras": {
                "shop": "supermarket",
            },
        }

        hours = json.loads(
            response.xpath(
                '//div[@class="c-hours-details-wrapper js-hours-table"]/@data-days'
            ).extract_first()
        )
        opening_hours = self.store_hours(hours) if hours else None
        if opening_hours:
            properties["opening_hours"] = opening_hours

        nav_links = response.xpath("//ul[@class='Navbar']/li/a/@href").getall()
        fuel_link = next((l for l in nav_links if "fuel" in l), None)

        if fuel_link:
            yield scrapy.Request(
                fuel_link, callback=self.add_fuel, meta={"properties": properties}
            )
        else:
            yield GeojsonPointItem(**properties)

    def add_fuel(self, response):
        properties = response.meta["properties"]
        services = response.xpath(
            "//ul[@class='Core-servicesList']//span[@itemprop='name']/text()"
        ).getall()

        properties["extras"].update(
            {"amenity:fuel": True, "fuel:diesel": "Diesel" in services}
        )

        yield GeojsonPointItem(**properties)
