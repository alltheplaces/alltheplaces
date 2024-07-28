import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class LonghornSteakhouseSpider(scrapy.Spider):
    name = "longhorn_steakhouse"
    item_attributes = {"brand": "LongHorn Steakhouse", "brand_wikidata": "Q3259007"}
    allowed_domains = []
    start_urls = [
        "https://www.longhornsteakhouse.com/locations-sitemap.xml",
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36 RuxitSynthetic/1.0 v2946028852165593646 t2919217341348717815",
    }
    download_delay = 0.3

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day, open_close = hour.split(" ")
            open_time, close_time = open_close.split("-")
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")
        return opening_hours.as_opening_hours()

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        store_data = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
        ).extract_first()
        if store_data:
            data = json.loads(store_data)
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

            # Handle store pages that are missing the application/ld+json data
            addr, city_state_zip, phone = response.xpath('//p[@id="info-link-webhead"]/text()').extract()
            city, state, postcode = re.search(r"(.*?),\s([A-Z]{2})\s([\d-]+)$", city_state_zip).groups()

            properties = {
                "name": data.get("name") or response.xpath('//h1[@class="style_h1"]/text()').extract_first().strip(),
                "ref": data["branchCode"] or ref,
                "addr_full": data["address"]["streetAddress"].strip() or addr.strip(),
                "city": data["address"]["addressLocality"] or city,
                "state": data["address"]["addressRegion"] or state,
                "postcode": data["address"]["postalCode"] or postcode,
                "country": data["address"]["addressCountry"],
                "phone": data.get("telephone") or phone.strip(),
                "website": data.get("url") or response.url,
                "lat": float(data["geo"]["latitude"]),
                "lon": float(data["geo"]["longitude"]),
            }

            hours = data.get("openingHours")
            if hours:
                store_hours = self.parse_hours(hours)
                properties["opening_hours"] = store_hours

            yield Feature(**properties)
