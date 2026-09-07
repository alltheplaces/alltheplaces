import json
import re
from html import unescape
from typing import AsyncIterator

import scrapy
from scrapy import Request

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature

# Present in the finder page's own store list but not real single-address stores: whole-region
# marketing markers for Guadeloupe/La Réunion (no street address, no Timetables, no Url).
# Confirmed by inspecting the raw data, not assumed - a real store elsewhere in the same list
# (e.g. a train-station concession) also has empty Timetables, so that alone isn't a safe filter.
EXCLUDED_REFS = {"989", "990"}
# Shared call-center/concession hotlines seen stamped on multiple, unrelated stores
# (main customer service line, and a separate one shared by several airport corners) -
# not per-location. Confirmed by spot-checking several stores' raw data, not assumed.
GENERIC_PHONES = {"0825020020", "0176276819"}
# A shared airport-concession contact, seen on 7 unrelated corner stores in a full-scale run.
GENERIC_EMAILS = {"customer-service@BuyPARIS.com"}
# httpResponseHeaders is required alongside httpResponseBody so scrapy-zyte-api can tell
# the response is HTML and build a TextResponse - without it, response.css() fails.
ZYTE_API_META = {"zyte_api": {"httpResponseBody": True, "httpResponseHeaders": True, "geolocation": "FR"}}


class FnacFRSpider(scrapy.Spider):
    name = "fnac_fr"
    item_attributes = {"brand": "Fnac", "brand_wikidata": "Q676585"}
    allowed_domains = ["fnac.com"]
    # The map widget on the store finder embeds the full national store list (address,
    # coordinates, structured hours) as a single data-stores attribute - one stable, general page
    # instead of depending on any one store's own page staying up.
    start_urls = ["https://www.fnac.com/localiser-magasin-fnac/w-4"]

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url, meta=ZYTE_API_META)

    def parse(self, response: scrapy.http.Response, **kwargs):
        stores_json = response.css(".js-StoreFinder-map::attr(data-stores)").get()
        if not stores_json:
            return
        for store in json.loads(unescape(stores_json))["Store"]:
            if store["EAGId"] in EXCLUDED_REFS:
                continue

            item = Feature()
            item["ref"] = store["EAGId"]
            item["branch"] = store.get("Name")
            item["street_address"] = ", ".join(
                line.strip(" ,") for line in store["AddressLine"].splitlines() if line.strip(" ,")
            )
            item["city"] = store["CityName"]
            item["postcode"] = store["ZipCode"]
            # Monaco is on the same fnac.com store list/postal range as mainland France but isn't France.
            item["country"] = "MC" if store["ZipCode"].startswith("980") else "FR"
            if url := store.get("Url"):
                item["website"] = url

            if m := re.match(r"\((-?[\d.]+),(-?[\d.]+)\)", store.get("Coord") or ""):
                item["lat"], item["lon"] = m.groups()

            oh = OpeningHours()
            for day in store.get("Timetables") or []:
                day_code = DAYS_FR.get(day["DayOfWeek"].capitalize())
                # Some stores close for lunch, giving two ranges in one string with no
                # separator, e.g. "09:30 - 12:30 14:00 - 19:00".
                times = re.findall(r"\d{1,2}:\d{2}", day.get("OpeningPeriods") or "")
                if day_code:
                    for open_time, close_time in zip(times[0::2], times[1::2]):
                        oh.add_range(day_code, open_time, close_time)
            item["opening_hours"] = oh

            if url:
                # Phone/email aren't in the finder's bulk data - only on the store's own page,
                # as Open Graph meta tags. Handle a dead link (seen before, Fnac's own 404s
                # exist) by still yielding the item without them, rather than losing it.
                yield Request(
                    url,
                    callback=self.parse_store_contact,
                    meta=ZYTE_API_META | {"item": item, "handle_httpstatus_list": [404]},
                )
            else:
                yield item

    def parse_store_contact(self, response: scrapy.http.Response, **kwargs):
        item = response.meta["item"]
        if response.status == 200:
            email = response.css('meta[property="og:email"]::attr(content)').get()
            if email and email not in GENERIC_EMAILS:
                item["email"] = email

            phone = response.css('meta[property="og:phone_number"]::attr(content)').get()
            if phone and (digits := re.match(r"^[\d\s]+", phone)):
                if digits.group().replace(" ", "") not in GENERIC_PHONES:
                    item["phone"] = phone
        yield item
