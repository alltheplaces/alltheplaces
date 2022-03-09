# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class FedExOfficeSpider(scrapy.Spider):
    name = "fedex_office_alt"
    item_attributes = {"brand": "FedEx Office"}
    allowed_domains = ["fedex.com"]
    download_delay = 0.2
    start_urls = [
        "https://local.fedex.com/sitemap/fedex-office-sitemap.xml",
        "https://local.fedex.com/sitemap/fedex-ship-center-sitemap.xml",
        "https://local.fedex.com/sitemap/fedex-freight-sitemap.xml",
        "https://local.fedex.com/sitemap/canada-fedex-ship-center-sitemap.xml",
        "https://local.fedex.com/sitemap/puerto-rico-fedex-ship-center-sitemap.xml",
        "https://local.fedex.com/sitemap/us-virgin-islands-fedex-ship-center-sitemap.xml",
    ]

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None or len(store_hours) == 0:
            return

        for store_day in store_hours:
            if store_day == "Closed":
                continue
            else:
                day_open, close_time = store_day.split("-")
                day = day_open.split(" ")[0]
                open_time = day_open.split(" ")[1]
                opening_hours.add_range(
                    day=day,
                    open_time=open_time.strip(),
                    close_time=close_time.strip(),
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        # Check if store is closed
        title = response.xpath('//div[@class="fx-copy"]/h1/text()').extract_first()
        store_is_closed = "This Location is No Longer Available"
        if title == store_is_closed:
            pass
        else:
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
            script_content = response.xpath(
                '//script[@type="text/javascript" and contains(text(), "current_location_point")]/text()'
            ).extract_first()
            store_data = json.loads(
                re.search(r"current_location_point = (.*);", script_content).group(1)
            )

            properties = {
                "ref": ref,
                "name": response.xpath(
                    'normalize-space(//*[@itemprop="name"]//text())'
                ).extract_first(),
                "addr_full": response.xpath(
                    'normalize-space(//span[@itemprop="streetAddress"]//text())'
                ).extract_first(),
                "city": response.xpath(
                    'normalize-space(//span[@itemprop="addressLocality"]//text())'
                ).extract_first(),
                "state": response.xpath(
                    'normalize-space(//span[@itemprop="addressRegion"]//text())'
                ).extract_first(),
                "postcode": response.xpath(
                    'normalize-space(//span[@itemprop="postalCode"]//text())'
                ).extract_first(),
                "country": response.xpath(
                    'normalize-space(//span[@itemprop="addressCountry"]//text())'
                ).extract_first(),
                "phone": response.xpath(
                    'normalize-space(//meta[@itemprop="telephone"]/@content)'
                ).extract_first(),
                "website": response.url,
                "lat": response.xpath(
                    'normalize-space(//meta[@itemprop="latitude"]/@content)'
                ).extract_first(),
                "lon": response.xpath(
                    'normalize-space(//meta[@itemprop="longitude"]/@content)'
                ).extract_first(),
                "extras": {
                    "branch_id": store_data.get("fxo_branch_id"),
                    "location_id": store_data.get("locid"),
                    "location_code": store_data.get("local_fdx_type"),
                    "location_type": store_data.get("location_type"),
                    "venue": store_data.get("bldg"),
                    "venue_note": store_data.get("loc_onprop"),
                },
            }

            hours = response.xpath(
                '//meta[@itemprop="openingHours"]/@content'
            ).extract()
            if hours:
                properties["opening_hours"] = self.parse_hours(hours)

            yield GeojsonPointItem(**properties)
