import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class UrbanOutfitters(SitemapSpider, StructuredDataSpider):
    download_delay = 10
    name = "urban_outfitters"
    item_attributes = {"brand": "Urban Outfitters", "brand_wikidata": "Q3552193"}
    allowed_domains = ["www.urbanoutfitters.com"]
    sitemap_urls = ["https://www.urbanoutfitters.com/store_sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        item["name"] = item["name"].split("-")[0].strip()

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
        item["opening_hours"] = oh
        yield item

    def parse_hours(self, hours):
        oh = OpeningHours()

        for h in hours:
            d = h.get("name")
            ot = h.get("openHour")
            ct = h.get("closeHour")
            # Some stores are permanently closed, thus no time is defined
            if not ot or not ct or ot == "Closed" or ct == "Closed":
                continue

            # Fix hour formatting
            ot = self.fix_hour(ot)
            ct = self.fix_hour(ct)

            days = self.parse_days(d)
            for day in days:
                oh.add_range(day=day, open_time=ot, close_time=ct, time_format="%I:%M %p")

        return oh.as_opening_hours()

    def fix_hour(self, h):
        """Parses hours and returns the desired format of "%I:%M %p"
        a) 10:30 PM, 9:00 AM
        b) 10pm, 9am
        c) 10:30pm, 9:00am
        """
        h_reg_a = re.compile(r"\d+:\d+ [AP]M")
        h_reg_b = re.compile(r"(\d+)([ap]m)")
        h_reg_c = re.compile(r"(\d+):(\d+)([ap]m)")

        h_a = h_reg_a.match(h)
        h_b = h_reg_b.match(h)
        h_c = h_reg_c.match(h)

        if h_a:
            return h

        if h_b:
            return f"{h_b.group(1)}:00 {h_b.group(2).upper()}"

        if h_c:
            return f"{h_c.group(1)}:{h_c.group(2)} {h_c.group(3).upper()}"

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
