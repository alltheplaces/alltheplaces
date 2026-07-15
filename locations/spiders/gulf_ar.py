import json
import re
import unicodedata
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines

BASE = "https://master.d3cm5183c0na8t.amplifyapp.com"


def gbp_time(value: dict | None) -> str:
    # The brand's own payload carries times in Google-Business-Profile shape,
    # {"hours": H, "minutes": M}; an absent component means zero, and hour 24 is
    # the end-of-day midnight boundary.
    value = value or {}
    hours = value.get("hours", 0)
    if hours >= 24:
        return "23:59"
    return "{:02d}:{:02d}".format(hours, value.get("minutes", 0))


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def service_present(value: Any) -> bool:
    # The services sheet uses "SI"/"NO", except Gomería (tyre service) which
    # repeats its own label instead of "SI"; treat anything but blank/"NO" as yes.
    return bool(value) and str(value).strip().upper() != "NO"


class GulfARSpider(Spider):
    name = "gulf_ar"
    item_attributes = {"brand": "Gulf", "brand_wikidata": "Q5617505"}
    # Gulf has no worldwide store locator; the Argentine network (run under
    # licence by DeltaPatagonia S.A.) is published on the brand's own site,
    # gulfcombustibles.com, via a multi-tenant Next.js locator. We scrape that
    # page: the station list is prerendered into the /gulf __NEXT_DATA__. The
    # records use the Google-Business-Profile schema because the brand manages its
    # listings there and its site republishes them (we never contact Google). The
    # per-site services (GNC, car wash, ATM, tyres, store) live in a separate
    # global table rendered only onto the city pages, keyed by PDV == storeCode.
    start_urls = [BASE + "/gulf"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = self.extract_next_data(response)["locations"]
        # Fetch one city page to read the global services table, then join it to
        # the full location list. The city is derived from a location so nothing
        # is hardcoded; an errback still yields the stations if that page fails.
        address = locations[0]["address"]
        city_url = "{}/gulf/argentina/{}/{}".format(
            BASE, slugify(address["administrativeArea"]), slugify(address["locality"])
        )
        yield response.follow(
            city_url,
            callback=self.parse_with_services,
            cb_kwargs={"locations": locations},
            errback=self.on_city_error,
        )

    def on_city_error(self, failure: Any) -> Any:
        # City page unreachable: still emit every station, just without services.
        self.logger.warning("services table fetch failed (%s); emitting stations without services", failure.value)
        yield from self.build_items(failure.request.cb_kwargs["locations"], {})

    def parse_with_services(self, response: Response, locations: list[dict]) -> Any:
        table = self.extract_next_data(response).get("respAdditional", {}).get("gulfServices", [])
        services = {}
        for row in table:
            row = {key.strip(): value for key, value in row.items()}
            services[str(row.get("Nro PDV", "")).strip()] = row
        yield from self.build_items(locations, services)

    def build_items(self, locations: list[dict], services: dict[str, dict]) -> Any:
        for location in locations:
            item = DictParser.parse(location)  # maps locality -> city, postalCode -> postcode, primaryPhone -> phone
            item.pop("name", None)  # DictParser sets this to the GBP resource path; NSI supplies name=Gulf
            item.pop("website", None)  # only the generic brand homepage, never a venue-specific URL
            item["ref"] = location["storeCode"]

            if not (item.get("phone") or "").strip().startswith("0"):
                item.pop("phone", None)  # drop bare local numbers with no Argentine area code (e.g. "491-3389")

            address = location["address"]
            item["street_address"] = merge_address_lines(address["addressLines"])
            item["state"] = address.get("administrativeArea")
            item["country"] = address.get("regionCode")
            item["lat"] = location["latlng"]["latitude"]
            item["lon"] = location["latlng"]["longitude"]
            item["opening_hours"] = self.parse_hours(location.get("regularHours"))

            apply_category(Categories.FUEL_STATION, item)
            entry = services.get(item["ref"])
            if entry:
                apply_yes_no(Fuel.CNG, item, service_present(entry.get("GNC")))
                apply_yes_no(Extras.CAR_WASH, item, service_present(entry.get("Lavadero")))
                apply_yes_no(Extras.ATM, item, service_present(entry.get("Cajero Automático")))
                apply_yes_no(Extras.TYRE_SERVICES, item, service_present(entry.get("Gomería")))
                # NB: the on-site "Gulf Store" is deliberately NOT tagged shop=convenience.
                # That is a top-level category tag, and NSI only matches a brand when the
                # item's categories are a subset of the brand's; Gulf's NSI entry is
                # amenity=fuel only, so adding shop=convenience breaks the brand match.
            yield item

    @staticmethod
    def extract_next_data(response: Response) -> dict:
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        return data["props"]["pageProps"]

    @staticmethod
    def parse_hours(regular_hours: dict | None) -> OpeningHours | str | None:
        periods = (regular_hours or {}).get("periods")
        if not periods:
            return None
        # GBP encodes a 24-hour day as an empty openTime with a closeTime of hour
        # 24; when every day is like that, the station is simply 24/7.
        if len(periods) == 7 and all(
            (p.get("closeTime") or {}).get("hours") == 24 and not (p.get("openTime") or {}) for p in periods
        ):
            return "24/7"
        oh = OpeningHours()
        for period in periods:
            if day := sanitise_day(period["openDay"]):
                oh.add_range(day, gbp_time(period.get("openTime")), gbp_time(period.get("closeTime")))
        return oh
