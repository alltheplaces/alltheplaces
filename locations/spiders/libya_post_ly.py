from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import bbox_contains
from locations.items import Feature

API_URL = "https://cons.libyapost.ly:54800/api/office?page={}"
# Public key baked into the libyapost.ly locator's JS bundle and sent by the site on every request
# (not an account credential); the API answers 401 without it.
HEADERS = {"X-APP-KEY": "pk_live_8e24b1a7f9c84310b32c8b49eaf1d712c7f9a3b4d5e6f708"}
# (min_lon, min_lat, max_lon, max_lat) of Libya, with a little slack.
LIBYA_BBOX = (9.3, 19.4, 25.2, 33.3)


class LibyaPostLySpider(Spider):
    name = "libya_post_ly"
    item_attributes = {"operator": "بريد ليبيا", "operator_wikidata": "Q56300507"}
    allowed_domains = ["cons.libyapost.ly"]
    # The API allows 60 requests a minute; the whole country is 11 pages.
    custom_settings = {"CONCURRENT_REQUESTS": 1, "DOWNLOAD_DELAY": 2}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=API_URL.format(1), headers=HEADERS)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        page = response.json()["data"]
        for office in page["data"]:
            if office.get("name_en") == "Test":
                continue  # a placeholder record without coordinates ("مكتب تجريبي", test office)
            yield self.parse_office(office)
        if page["current_page"] == 1:
            for page_number in range(2, page["last_page"] + 1):
                yield JsonRequest(url=API_URL.format(page_number), headers=HEADERS)

    def parse_coordinates(self, lat: str | None, lon: str | None) -> tuple[float | None, float | None]:
        if not lat or not lon:
            return None, None
        # A block of eastern (Green Mountain) offices stores degrees-minutes-seconds packed into a
        # decimal string ("32.4623" = 32°46'23"), always with at most four significant decimals;
        # genuine decimal coordinates in this API carry five or more.
        if all(len(value.split(".")[-1].rstrip("0")) <= 4 for value in (lat, lon)):
            packed = [self.unpack_dms(value) for value in (lat, lon)]
            if None not in packed:
                self.crawler.stats.inc_value("atp/{}/coordinates/packed_dms".format(self.name))
                lat_f, lon_f = packed
            else:
                lat_f, lon_f = float(lat), float(lon)
        else:
            lat_f, lon_f = float(lat), float(lon)
        if bbox_contains(LIBYA_BBOX, (lon_f, lat_f)):
            return lat_f, lon_f
        if bbox_contains(LIBYA_BBOX, (lat_f, lon_f)):  # latitude and longitude entered the wrong way round
            self.crawler.stats.inc_value("atp/{}/coordinates/swapped".format(self.name))
            return lon_f, lat_f
        # Several southern (Fezzan) offices carry placeholder values far outside Libya.
        self.crawler.stats.inc_value("atp/{}/coordinates/outside_libya".format(self.name))
        return None, None

    @staticmethod
    def unpack_dms(value: str) -> float | None:
        degrees, _, fraction = value.partition(".")
        fraction = (fraction + "0000")[:4]
        minutes, seconds = int(fraction[:2]), int(fraction[2:])
        if minutes >= 60 or seconds >= 60:
            return None
        return int(degrees) + minutes / 60 + seconds / 3600

    def parse_office(self, office: dict) -> Feature:
        item = Feature()
        item["ref"] = str(office["id"])
        item["lat"], item["lon"] = self.parse_coordinates(office.get("latitude"), office.get("longitude"))
        item["branch"] = (office.get("name_ar") or "").strip() or None
        item["extras"] = {"operator:en": "Libya Post"}
        if name_en := (office.get("name_en") or "").strip():
            item["extras"]["branch:en"] = name_en
        item["postcode"] = office.get("postal_code")
        item["phone"] = office.get("phone_number")
        item["street_address"] = (
            ", ".join(filter(None, [office.get("address_line1"), office.get("address_line2")])) or None
        )
        if city := office.get("city"):
            item["city"] = city.get("name")
            if city.get("name_en"):
                item["extras"]["addr:city:en"] = city["name_en"]
            if region := city.get("region"):
                item["state"] = region.get("name")
        apply_category(Categories.POST_OFFICE, item)
        return item
