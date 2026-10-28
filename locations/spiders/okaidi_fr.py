import csv
import gzip
import json
import re
from collections import defaultdict
from typing import Any, Iterable

from scrapy.http import FormRequest, Request, Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines
from locations.searchable_points import get_searchable_points_path
from locations.user_agents import FIREFOX_LATEST


class OkaidiFRSpider(SitemapSpider):
    name = "okaidi_fr"
    item_attributes = {"brand": "Okaïdi", "brand_wikidata": "Q3350027"}
    sitemap_urls = ["https://www.okaidi.fr/sitemap-stores.xml"]
    custom_settings = {
        # Akamai returns 403 without these two headers, and to Firefox 140 (BROWSER_DEFAULT as of 2026-10).
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
        },
        "USER_AGENT": FIREFOX_LATEST,
        # Some city URLs redirect to the store finder, listed in robots.txt as /shop/locateshop: see parse().
        "REDIRECT_ENABLED": False,
    }
    handle_httpstatus_list = [301, 302]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.communes = defaultdict(set)
        with gzip.open(get_searchable_points_path("postcodes/frzips.csv.gz"), mode="rt", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["lat"] and row["lng"]:
                    # Paris, Lyon and Marseille are listed per arrondissement ("PARIS 01").
                    name = re.sub(r" \d\d$", "", row["Nom_commune"])
                    self.communes[self.commune_key(name)].add((row["lat"], row["lng"]))

    @staticmethod
    def commune_key(name: str) -> str:
        name = re.sub(r"['-]", " ", name.upper())
        name = re.sub(r"\bSAINT(E?)\b", r"ST\1", name)
        return name.replace(" ", "")

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature | Request]:
        if response.status == 200:
            if isinstance(shop := self.extract_shops(response), dict):
                yield self.parse_shop(shop)
            return
        location = response.headers.get("Location") or b""
        if not location.endswith(b"/Shop/LocateShop"):
            yield response.follow(location.decode(), self.parse)
            return
        # oxybul.com serves the same store finder, and its robots.txt allows it.
        slug = response.url.rsplit("/", 1)[-1]
        points = self.communes.get(self.commune_key(slug.removeprefix("okaidi-")), set())
        if not points:
            self.logger.error("No coordinates found for %s", slug)
        # Searched by coordinates: the store finder geocodes city names unreliably.
        for latitude, longitude in points:
            # The store finder returns 403 to a POST without the Referer header that Scrapy adds here.
            yield FormRequest(
                "https://www.oxybul.com/Shop/LocateShop",
                formdata={"latitude": latitude, "longitude": longitude, "vendorIds": "2", "submitType": "1"},
                callback=self.parse_search,
                cb_kwargs={"slug": slug},
            )

    def parse_search(self, response: Response, slug: str) -> Iterable[Feature]:
        for shop in self.extract_shops(response) or []:
            # Results include nearby shops of other cities and countries.
            if shop.get("SeName") == slug:
                yield self.parse_shop(shop)

    def extract_shops(self, response: Response) -> Any:
        if match := re.search(r"var DataStore = ", response.text):
            return json.JSONDecoder().raw_decode(response.text, match.end())[0].get("ShopsResult")
        return None

    def parse_shop(self, shop: dict) -> Feature:
        item = Feature()
        item["ref"] = shop["ShopCode"]
        item["branch"] = shop["Name"]
        item["website"] = f"https://www.okaidi.fr/Shop/{shop['SeName']}/{shop['Id']}"
        item["lat"] = shop.get("Latitude")
        item["lon"] = shop.get("Longitude")
        # Address1 is the brand and shop name; Address3 mostly names the shopping centre.
        item["street_address"] = merge_address_lines([shop.get("Address2"), shop.get("Address3")])
        item["city"] = shop.get("City")
        item["postcode"] = shop.get("PostalCode")
        item["country"] = shop.get("Country")
        item["phone"] = shop.get("Phone")
        item["email"] = shop.get("Email")

        oh = OpeningHours()
        for time_frame in shop.get("ShopTimeFrames") or []:
            # The site only displays the days that have a schedule: the others are left unset, not closed.
            schedule = time_frame.get("NormalSchedule") or ""
            for open_time, close_time in re.findall(r"(\d\d:\d\d)-(\d\d:\d\d)", schedule):
                oh.add_range(DAYS[time_frame["DayOfWeek"] - 1], open_time, close_time)
        item["opening_hours"] = oh

        if shop.get("IsActive") is False:
            set_closed(item)
        return item
