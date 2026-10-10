import html
import re
from collections import defaultdict
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature


class StartPeopleBESpider(Spider):
    name = "start_people_be"
    item_attributes = {"brand": "Start People", "brand_wikidata": "Q2646530"}
    allowed_domains = ["www.startpeople.be"]
    start_urls = ["https://www.startpeople.be/fr/agences/"]
    # One marker per office in the listing page's map script.
    marker = re.compile(r'lat: ([-\d.]+), lng: ([-\d.]+).+?title: "([^"]*)".+?<p>(.*?)</p>.+?href="([^"]+)"', re.S)

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Request]:
        # The Dutch pages are the complete ones. The French listing is only read for the French
        # URLs, which cannot be derived from the Dutch ones.
        french_urls = {
            (lat, lon, address): response.urljoin(url)
            for lat, lon, _, address, url in self.marker.findall(response.text)
        }
        yield response.follow("/nl/kantoren/", self.parse_offices, cb_kwargs={"french_urls": french_urls})

    def parse_offices(self, response: Response, french_urls: dict) -> Iterable[Request]:
        # Coordinates are only in the listing's map script, contact details only on office pages.
        offices_by_name = defaultdict(list)
        for lat, lon, name, address, url in self.marker.findall(response.text):
            item = Feature()
            item["ref"] = url.rstrip("/").split("/")[-1]
            item["lat"], item["lon"] = lat, lon
            item["branch"] = html.unescape(name).removeprefix("Start People ").title()
            street_address, _, postcode_city = html.unescape(address).rpartition(",")
            item["street_address"] = street_address.strip()
            item["postcode"], _, city = postcode_city.strip().partition(" ")
            item["city"] = city.title()
            item["website"] = item["extras"]["website:nl"] = response.urljoin(url)
            if french_url := french_urls.get((lat, lon, address)):
                item["extras"]["website:fr"] = french_url
            offices_by_name[name].append(item)
        # One request per office name; its other pages, if any, are fetched in turn.
        for offices in offices_by_name.values():
            yield Request(
                offices[0]["website"], self.parse_office, cb_kwargs={"item": offices[0], "others": offices[1:]}
            )

    def parse_office(
        self, response: Response, item: Feature, others: list[Feature], kept: list[tuple] | None = None
    ) -> Iterable[Request | Feature]:
        # Phone, email and hours are given per specialisation: the first one is published.
        contacts = set()
        for block in response.css(".dxp-page-office-icons-content"):
            phone = block.css('a[href^="tel:"]::attr(href)').get()
            email = block.css('a[href^="mailto:"]::attr(href)').get()
            if phone or email:
                contacts.add((block.css("h3::text").get(), phone, email))
            if not phone or item.get("phone"):
                continue
            item["phone"] = phone.removeprefix("tel:")
            item["email"] = (email or "").removeprefix("mailto:")
            oh = OpeningHours()
            by_appointment = []
            for row in block.css(".dxp-page-office--opening-hours tr"):
                day = DAYS_NL.get(row.css("td::text").get("").strip().title())
                hours = " ".join(row.css("td:last-child::text").getall())
                if not day:
                    continue
                if "gesloten" in hours:
                    oh.set_closed(day)
                if "op afspraak" in hours:
                    by_appointment.append(day)
                for open_time, close_time in re.findall(r"(\d\d:\d\d) - (\d\d:\d\d)", hours):
                    oh.add_range(day, open_time, close_time)
            if by_appointment:
                # "By appointment" is kept as a comment, which OpeningHours cannot carry.
                item["opening_hours"] = ", ".join(
                    filter(None, ['{} "op afspraak"'.format(",".join(by_appointment)), oh.as_opening_hours()])
                )
            elif oh.day_hours:
                item["opening_hours"] = oh
        apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)

        # An office that moved is still listed at its old address: drop a page whose contacts
        # are all on another page of the same name.
        kept = kept or []
        if not any(contacts <= other_contacts for _, other_contacts in kept):
            kept = [office for office in kept if not office[1] <= contacts] + [(item, contacts)]
        if others:
            yield Request(
                others[0]["website"],
                self.parse_office,
                cb_kwargs={"item": others[0], "others": others[1:], "kept": kept},
            )
            return
        for office, _ in kept:
            yield office
