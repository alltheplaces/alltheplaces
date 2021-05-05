# -*- coding: utf-8 -*-
import json
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class LuLuLemonSpider(scrapy.Spider):
    download_delay = 0.1
    name = "lululemon"
    item_attributes = {"brand": "LuLuLemon", "brand_wikidata": "Q6702957"}
    allowed_domains = ["shop.lululemon.com"]
    start_urls = ("https://shop.lululemon.com/stores/all-lululemon-stores",)

    def parse(self, response):
        urls = response.xpath('//a[@class="store-link basic"]/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse_store(self, response):
        address = {}
        geo = {}
        data = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        )

        ref = response.xpath('//h1[@class="lll-stack-lvl4"]/text()').extract_first()

        if data.get("address"):
            address["full"] = data["address"].get("streetAddress")
            address["zip"] = data["address"].get("postalCode")
            address["state"] = data["address"].get("addressRegion")
            address["city"] = data["address"].get("addressLocality")
            address["country"] = data["address"].get("addressCountry")
        if data.get("geo"):
            geo["lat"] = data["geo"].get("latitude")
            geo["lon"] = data["geo"].get("longitude")
        oh = self.parse_hours(data.get("openingHours"))
        if not oh:
            ref = "CLOSED - {}".format(ref)

        properties = {
            "addr_full": address.get("full"),
            "phone": data.get("telephone"),
            "city": address.get("city"),
            "state": address.get("state"),
            "postcode": address.get("zip"),
            "ref": ref,
            "website": response.url,
            "lat": geo.get("lat"),
            "lon": geo.get("lon"),
            "opening_hours": oh,
        }
        yield GeojsonPointItem(**properties)

    def parse_hours(self, hours):
        oh = OpeningHours()

        for h in hours:
            t = h.replace(" - ", "-")
            d, h = t.split()
            ot, ct = h.split("-")
            # Some stores are permanently closed, thus no time is defined
            if ot == "null" or ct == "null":
                continue
            days = self.parse_days(d)
            for day in days:
                oh.add_range(day=day, open_time=ot, close_time=ct, time_format="%H:%M")

        return oh.as_opening_hours()

    def parse_days(self, days):
        """Parse day ranges and returns a list of days it represent
        The following formats are considered:
          - Single day, e.g. "Mon", "Monday"
          - Range, e.g. "Mon-Fri", "Tue-Sund", "Sat-Sunday"
          - Two days, e.g. "Sat & Sun", "Friday & Su"

        Returns a list with the weekdays
        """
        # Produce a list of weekdays between two days e.g. su-sa, mo-th, etc.
        if "-" in days:
            d = days.split("-")
            r = [i.strip()[:2] for i in d]
            s = WEEKDAYS.index(r[0].title())
            e = WEEKDAYS.index(r[1].title())
            if s <= e:
                return WEEKDAYS[s : e + 1]
            else:
                return WEEKDAYS[s:] + WEEKDAYS[: e + 1]
        # Two days
        if "&" in days:
            d = days.split("&")
            return [i.strip()[:2].title() for i in d]
        # Single days
        else:
            return [days.strip()[:2].title()]
