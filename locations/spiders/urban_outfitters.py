# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

US_STATES = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DC",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]


class UrbanOutfitters(scrapy.Spider):
    download_delay = 1.2
    name = "urban_outfitters"
    item_attributes = {"brand": "Urban Outfitters", "brand_wikidata": "Q3552193"}
    allowed_domains = ["www.urbanoutfitters.com"]
    start_urls = ("https://www.urbanoutfitters.com/stores/",)

    def parse(self, response):
        urls = response.xpath(
            '//li[@itemtype="http://www.schema.org/SiteNavigationElement"]/a[starts-with(@href,"/stores/")]/@href'
        ).extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse_store(self, response):
        state = response.xpath(
            '//span[@itemprop="addressRegion"]/text()'
        ).extract_first()

        # Only scrape US locations as non-us locations have differences
        if not state in US_STATES:
            return

        street_address = response.xpath(
            '//span[@itemprop="streetAddress"]/text()'
        ).extract_first()
        city = response.xpath(
            '//span[@itemprop="addressLocality"]/text()'
        ).extract_first()
        postcode = response.xpath(
            '//span[@itemprop="postalCode"]/text()'
        ).extract_first()
        phone = response.xpath('//span[@itemprop="telephone"]/text()').extract_first()
        lat = response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
        lon = response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
        title = response.xpath('//h1[@itemprop="name"]/text()').extract_first()

        # There's a 301 that returns back to /stores/ we return earlier to avoid errors
        if not title:
            print(response.url)
            return

        store_name = title.split("-")[0].strip()
        raw_hours = response.xpath("//li/text()").extract()
        raw_hours = [h.strip() for h in raw_hours if h.strip()]
        hours = []
        for h in raw_hours:
            entry = {}
            hrs = " ".join(h.split(" ")[1:])
            entry["name"] = h.split(" ")[0].strip(":")
            entry["openHour"] = hrs.split("-")[0].strip()
            entry["closeHour"] = hrs.split("-")[1].strip()
            hours.append(entry)
        oh = self.parse_hours(hours)
        properties = {
            "addr_full": street_address,
            "phone": phone,
            "city": city,
            "state": state,
            "postcode": postcode,
            "ref": store_name,
            "website": response.url,
            "lat": lat,
            "lon": lon,
            "opening_hours": oh,
        }
        yield GeojsonPointItem(**properties)

    def parse_hours(self, hours):
        oh = OpeningHours()

        for h in hours:
            d = h.get("name")
            ot = h.get("openHour")
            ct = h.get("closeHour")
            # Some stores are permanently closed, thus no time is defined
            if not ot or not ct or ot == "Closed" or ct == "Closed":
                continue
            days = self.parse_days(d)
            for day in days:
                oh.add_range(
                    day=day, open_time=ot, close_time=ct, time_format="%I:%M %p"
                )

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
        DAYS_OF_WEEK = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        if "-" in days:
            d = days.split("-")
            r = [i.strip()[:2] for i in d]
            s = DAYS_OF_WEEK.index(r[0].title())
            e = DAYS_OF_WEEK.index(r[1].title())
            if s <= e:
                return DAYS_OF_WEEK[s : e + 1]
            else:
                return DAYS_OF_WEEK[s:] + DAYS_OF_WEEK[: e + 1]
        # Two days
        if "&" in days:
            d = days.split("&")
            return [i.strip()[:2].title() for i in d]
        # Single days
        else:
            return [days.strip()[:2].title()]
