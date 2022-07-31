# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem
import datetime

DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thur": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
    "Mon-Fri": "Mo-Fr",
    "Mon-Sat": "Mo-Sa",
    "Mon-Thu": "Mo-Th",
    "Fri-Sat": "Fr-Sa",
    "Thu-Fri": "Th-Fr",
    "Mon-Wed": "Mo-We",
    "Thu-Sat": "Th-Sa",
}


class HomeDepotSpider(scrapy.Spider):
    name = "homedepot"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["www.homedepot.com"]
    start_urls = ("https://www.homedepot.com/l/storeDirectory",)
    download_delay = 0.2

    def store_hours(self, hours):
        o_hours = []

        for i in hours:
            times = re.search(r"(.+?) (.*)-(.+)", i).groups()

            days_data = times[0].strip().replace("{[", "")
            start = times[1].strip()
            end = times[2].strip().replace('"', "").replace("]}", "")

            start = datetime.datetime.strptime(start, "%I:%M %p").strftime("%H:%M")
            end = datetime.datetime.strptime(end, "%I:%M %p").strftime("%H:%M")
            days = DAY_MAPPING[days_data]

            opening_hours = "%s %s-%s" % (days, start, end)
            o_hours.append(opening_hours)

        return "; ".join(o_hours)

    def parse(self, response):
        urls = response.xpath(
            '//a[contains(@class,"store-directory__state-link")]/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        state_urls = response.xpath(
            '//div[contains(@class,"store-directory__store")]/a[1]/@href'
        ).extract()
        for state_url in state_urls:
            yield scrapy.Request(response.urljoin(state_url), callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        # the coordinates are stored inside an inline script element
        script_content = response.xpath(
            '//script[contains(text(),"coordinates")]/text()'
        ).extract_first()
        coord_data = re.search(
            r'"coordinates":(.*?}),',
            script_content.replace('"__typename":"Coordinates",', ""),
            flags=re.IGNORECASE | re.DOTALL,
        ).group(1)
        coords = json.loads(coord_data)

        # parse the JSON-LD data
        json_ld = json.loads(
            response.xpath(
                '//script[@id="thd-helmet__script--storeDetailStructuredLocalBusinessData"]/text()'
            ).extract_first()
        )

        properties = {
            "phone": json_ld["telephone"],
            "website": response.request.url,
            "ref": ref,
            "name": json_ld["name"],
            "addr_full": json_ld["address"]["streetAddress"],
            "postcode": json_ld["address"]["postalCode"],
            "state": json_ld["address"]["addressRegion"],
            "city": json_ld["address"]["addressLocality"],
            "lon": float(coords.get("lng")),
            "lat": float(coords.get("lat")),
        }

        opening_hours = self.store_hours(json_ld["openingHours"])
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)
