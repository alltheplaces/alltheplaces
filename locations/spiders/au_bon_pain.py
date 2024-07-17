import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class AuBonPainSpider(scrapy.Spider):
    name = "au_bon_pain"
    item_attributes = {"brand": "Au Bon Pain", "brand_wikidata": "Q4818942"}
    allowed_domains = [
        "www.aubonpain.com",
    ]
    start_urls = ("https://www.aubonpain.com/stores/all-stores",)

    def parse_hours(self, items):
        opening_hours = OpeningHours()

        for day in items:
            open_time = day["Open"]
            close_time = day["Close"]
            if close_time == "Closed" or open_time == "Closed":
                continue
            elif close_time == "Open 24 Hrs" or open_time == "Open 24 Hrs":
                open_time = "12:00 AM"
                close_time = "12:00 AM"
            elif close_time == "Open for Special Events":
                continue

            opening_hours.add_range(
                day=day["Day"][:2],
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M %p",
            )
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        ref = re.findall(r"[^(\/)]+$", response.url)[0]

        scripts = "".join(response.xpath("//script/text()").extract())
        lat, lon = re.search(r".*Microsoft.Maps.Location\(([0-9.-]*),\s+([0-9-.]*)\).*", scripts).groups()

        address1, address2 = response.xpath('//dt[contains(text(), "Address")]/following-sibling::dd/text()').extract()
        city, state, zipcode = re.search(r"^(.*),\s+([a-z]{2})\s+([0-9]+)$", address2.strip(), re.IGNORECASE).groups()

        properties = {
            "street_address": address1.strip(", "),
            "phone": response.xpath('//dt[contains(text(), "Phone")]/following-sibling::dd/a/text()').extract_first(),
            "city": city,
            "state": state,
            "postcode": zipcode,
            "ref": ref,
            "website": response.url,
            "lat": float(lat),
            "lon": float(lon),
        }
        hours = json.loads(re.search(r".*var\shours\s*=\s*(.*?);.*", scripts).groups()[0])
        hours = self.parse_hours(hours)
        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

    def parse(self, response):
        urls = response.xpath('//section/div/div//a[contains(@href, "stores")]/@href').extract()

        for url in urls:
            url = url.replace("\r\n", "")
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
