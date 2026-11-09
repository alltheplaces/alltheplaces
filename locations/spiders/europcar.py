import json
import re
from datetime import date, timedelta
from typing import Any, AsyncIterator, Iterable
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class EuropcarSpider(Spider):
    name = "europcar"
    item_attributes = {"brand": "Europcar", "brand_wikidata": "Q1376256"}
    # The station API never answers Scrapy's default "Accept-Language: en".
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept-Language": "en-US"}}
    # National sites, with the locale their station pages are published in.
    SITES = {
        "AT": ("de-AT", "www.europcar.at"),
        "AU": ("en-AU", "www.europcar.com.au"),
        "BE": ("fr-BE", "www.europcar.be"),
        "CH": ("de-CH", "www.europcar.ch"),
        "DE": ("de-DE", "www.europcar.de"),
        "ES": ("es-ES", "www.europcar.es"),
        "FI": ("fi-FI", "www.europcar.fi"),
        "FR": ("fr-FR", "www.europcar.fr"),
        "GB": ("en-GB", "www.europcar.co.uk"),
        "IE": ("en-IE", "www.europcar.ie"),
        "IT": ("it-IT", "www.europcar.it"),
        "NO": ("nb-NO", "www.europcar.no"),
        "NZ": ("en-NZ", "www.europcar.co.nz"),
        "PT": ("pt-PT", "www.europcar.pt"),
        "SE": ("sv-SE", "www.europcar.se"),
    }
    DEFAULT_SITE = ("en-US", "www.europcar.com")

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://www.europcar.com/en-us", callback=self.parse_config)

    def parse_config(self, response: Response) -> Any:
        # The sitemap lists under a quarter of the station pages; the CMS behind them lists all.
        if token := re.search(r'ctfAccessTokenCda:"([^"]+)"', response.text):
            yield self.make_station_list_request(token.group(1), 0, {})
        else:
            self.logger.error("Contentful token not found on %s", response.url)

    def make_station_list_request(self, token: str, skip: int, slugs: dict) -> JsonRequest:
        params = {
            "content_type": "osStationGeoPage",
            # Every locale, as the slug of a station page differs from one national site to another.
            "locale": "*",
            "select": "fields.slug,fields.stationCode",
            # Paging is only stable with an explicit order.
            "order": "sys.id",
            "limit": 1000,
            "skip": skip,
        }
        return JsonRequest(
            "https://cdn.contentful.com/spaces/wmdwnw6l5vg5/environments/master/entries?"
            + urlencode(params, safe="*,"),
            headers={"Authorization": f"Bearer {token}"},
            callback=self.parse_station_list,
            cb_kwargs={"token": token, "slugs": slugs},
        )

    def parse_station_list(self, response: Response, token: str, slugs: dict) -> Any:
        result = json.loads(response.text)
        for entry in result["items"]:
            # With every locale requested, each field is a dict keyed by locale.
            code = entry["fields"]["stationCode"]["en-US"].strip()
            slugs.setdefault(code, {}).update(entry["fields"].get("slug", {}))
        if result["skip"] + result["limit"] < result["total"]:
            yield self.make_station_list_request(token, result["skip"] + result["limit"], slugs)
            return
        for code, station_slugs in slugs.items():
            yield JsonRequest(
                f"https://api.aws.emobg.io/stationsearchapi/v1/stations/{code}",
                callback=self.parse_station,
                cb_kwargs={"slugs": station_slugs},
            )

    def parse_station(self, response: Response, slugs: dict) -> Iterable[Feature]:
        station = json.loads(response.text)
        # Internal stations are closed or back-office entries.
        if station.get("visibility") != "PUBLIC":
            return
        # Hours starting later mean a station not open yet, or closed for the season.
        # The margin covers the API's unknown timezone.
        weeks = station.get("openWeeks") or []
        if weeks and weeks[0]["startDate"] > (date.today() + timedelta(days=1)).isoformat():
            return
        address = station["contact"]["address"]

        item = Feature()
        item["ref"] = station["id"]
        item["branch"] = station["information"].get("name")
        item["street_address"] = merge_address_lines(address.get("streetLines", []))
        item["city"] = address.get("city")
        item["postcode"] = address.get("postCode")
        # "DB" is Europcar's own market code for Dubai and the northern emirates.
        item["country"] = "AE" if address.get("countryCode") == "DB" else address.get("countryCode")
        # "+33 (0) 0384761848": the trunk prefix is given twice.
        item["phone"] = re.sub(r"\(0\) 0?", "", station["contact"].get("phoneNumber") or "")
        item["lat"] = station.get("geoPosition", {}).get("lat")
        item["lon"] = station.get("geoPosition", {}).get("lng")
        locale, host = self.SITES.get(item["country"], self.DEFAULT_SITE)
        if locale not in slugs:
            locale, host = self.DEFAULT_SITE
        if slug := slugs.get(locale):
            item["website"] = f"https://{host}/{locale.lower()}/places/{slug}"

        if weeks:
            try:
                oh = OpeningHours()
                for day in weeks[0]["days"]:
                    for hours in day.get("Hours", []):
                        # "AFTER" ranges are a paid out-of-hours service, not opening hours.
                        if hours.get("businessType") == "NORMAL":
                            oh.add_range(day["codeDay"], hours["startHour"], hours["endHour"])
                item["opening_hours"] = oh
            except (KeyError, ValueError):
                self.logger.warning("Unreadable opening hours for station %s", item["ref"])

        apply_category(Categories.CAR_RENTAL, item)
        yield item
