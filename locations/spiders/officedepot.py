# -*- coding: utf-8 -*-
import json
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class OfficedepotSpider(scrapy.Spider):
    name = "officedepot"
    allowed_domains = ["where2getit.com"]

    def start_requests(self):
        url = "https://locations.where2getit.com/officedepot/rest/getlist?like=0.9145201524205426&lang=en_US"

        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://hosted.where2getit.com",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://hosted.where2getit.com/officedepot/2015/index1.html",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
        }

        form_data = {
            "request": {
                "appkey": "592778B0-A13B-11EB-B3DB-84030D516365",
                "formdata": {
                    "order": "city",
                    "objectname": "Locator::Store",
                    "softmatch": "1",
                    "where": {},
                },
            }
        }

        yield scrapy.http.FormRequest(
            url=url,
            method="POST",
            body=json.dumps(form_data),
            headers=headers,
            callback=self.parse,
        )

    def parse_store(self, response):
        o = OpeningHours()
        for d in response.xpath('//time[@itemprop="openingHours"]/@datetime').extract():
            day, times = d.split(" ", 1)
            s, f = times.split("-")

            # They seem to have a bug where they put down 24:00 when they mean noon
            if s == "24:00":
                s = "12:00"

            o.add_range(day, s, f)

        store_number_results = response.xpath('//dt[@class="lsp_number"]/text()')
        if store_number_results:
            ref = store_number_results[-1].extract().strip()

        yield GeojsonPointItem(
            lat=response.xpath('//meta[@itemprop="latitude"]/@content').extract_first(),
            lon=response.xpath(
                '//meta[@itemprop="longitude"]/@content'
            ).extract_first(),
            phone=response.xpath('//p[@itemprop="telephone"]/text()').extract_first(),
            addr_full=response.xpath(
                '//p[@itemprop="streetAddress"]/text()'
            ).extract_first(),
            city=response.xpath(
                '//p[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            state=response.xpath(
                '//p[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            postcode=response.xpath(
                '//p[@itemprop="postalCode"]/text()'
            ).extract_first(),
            website=response.url,
            ref=ref,
            opening_hours=o.as_opening_hours(),
        )

    def parse(self, response):
        data = response.json()

        for store in data["response"]["collection"]:
            properties = {
                "ref": store["clientkey"],
                "name": store.get("name"),
                "addr_full": store["address1"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["postalcode"],
                "country": store["country"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "phone": store["phone"],
            }

            yield GeojsonPointItem(**properties)
