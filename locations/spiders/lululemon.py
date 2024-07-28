import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature

WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class LululemonSpider(SitemapSpider):
    name = "lululemon"
    item_attributes = {"brand": "Lululemon", "brand_wikidata": "Q6702957"}
    sitemap_urls = ("https://shop.lululemon.com/sitemap.xml",)
    sitemap_rules = [
        (r"^https://shop.lululemon.com/stores/[^/]+/[^/]+/[^/]+$", "parse_store"),
    ]

    def parse_store(self, response):
        address = {}
        geo = {}
        hours = {}
        status = "CLOSED"
        data = json.loads(response.xpath('//script[@type="application/json"]/text()').extract_first())

        ref = data["props"]["pageProps"]["storeData"]["name"]
        address["full"] = data["props"]["pageProps"]["storeData"].get("fullAddress")
        address["zip"] = address["full"].split(",")[-1].strip()
        address["state"] = data["props"]["pageProps"]["storeData"].get("state")
        address["city"] = data["props"]["pageProps"]["storeData"].get("city")
        address["country"] = data["props"]["pageProps"]["storeData"].get("country")
        address["phone"] = data["props"]["pageProps"]["storeData"].get("phone")
        geo["lat"] = data["props"]["pageProps"]["storeData"].get("latitude")
        geo["lon"] = data["props"]["pageProps"]["storeData"].get("longitude")
        hours = data["props"]["pageProps"]["storeData"].get("hours")
        if data["props"]["pageProps"]["storeData"].get("status") == "active_soon":
            status = "Opening soon"

        oh = self.parse_hours(hours)
        if not oh:
            ref = "{} - {}".format(status, ref)

        properties = {
            "addr_full": address.get("full"),
            "phone": address.get("phone"),
            "city": address.get("city"),
            "state": address.get("state"),
            "postcode": address.get("zip"),
            "ref": ref,
            "website": response.url,
            "lat": geo.get("lat"),
            "lon": geo.get("lon"),
            "opening_hours": oh,
        }
        yield Feature(**properties)

    def parse_hours(self, hours):
        oh = OpeningHours()

        for h in hours:
            d = h.get("name")
            ot = h.get("openHour")
            ct = h.get("closeHour")
            # Some stores are permanently closed, thus no time is defined
            if not ot or not ct:
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
