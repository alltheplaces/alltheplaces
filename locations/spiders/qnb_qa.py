import re
from typing import Any, AsyncIterator

from scrapy import Selector, Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

ENDPOINT = "https://www.qnb.com/sites/Satellite/"
LATITUDE_RE = re.compile(r'var latitude\s*=\s*"([0-9.-]+)"')
LONGITUDE_RE = re.compile(r'var longitude\s*=\s*"([0-9.-]+)"')
# Each map marker's info window is emitted separately from its coordinates, so
# coordinates are matched back to the nearest preceding lat/lon assignment.
INFO_WINDOW_RE = re.compile(r"locationsDetail\s*=\s*'(<div class=\"info-window-content\".*?)'", re.S)


class QnbQASpider(Spider):
    name = "qnb_qa"
    item_attributes = {"brand": "QNB", "brand_wikidata": "Q1136759"}
    requires_proxy = "QA"  # Qatar-only site; other-country IPs can't reach it (Zyte returns 421)

    async def start(self) -> AsyncIterator[Any]:
        yield FormRequest(
            url=ENDPOINT,
            formdata={
                "pagename": "GetATMBranchResult",
                "site": "QNBQatar",
                "locale": "ar",
                "isatm": "false",
                "hasCity": "true",
                "countryId": "قطر",
                "cityId": "",
            },
            callback=self.parse_cities,
        )

    def parse_cities(self, response: Response, **kwargs: Any) -> Any:
        for city in response.xpath("//option/@value").getall():
            if not (city := city.strip()):
                continue
            for location_type in ("branch", "atm"):
                yield FormRequest(
                    url=ENDPOINT,
                    formdata={
                        "pagename": "GetATMBranchResult",
                        "site": "QNBQatar",
                        "locale": "ar",
                        "isatm": "true" if location_type == "atm" else "false",
                        "hasBranch": "true",
                        "cityId": city,
                    },
                    callback=self.parse_locations,
                    cb_kwargs={"city": city, "location_type": location_type},
                )

    def parse_locations(self, response: Response, city: str, location_type: str, **kwargs: Any) -> Any:
        text = response.text
        latitudes = [(m.start(), m.group(1)) for m in LATITUDE_RE.finditer(text)]
        longitudes = [(m.start(), m.group(1)) for m in LONGITUDE_RE.finditer(text)]

        # Map markers hold name/coordinates; the address list is rendered in a
        # separate block in the same order, so it is joined back positionally.
        windows = list(INFO_WINDOW_RE.finditer(text))
        address_spans = response.xpath('//span[strong[contains(text(), "العنوان")]]/following-sibling::span[1]')
        addresses = [" ".join("".join(span.xpath(".//text()").getall()).split()) for span in address_spans]
        if len(addresses) != len(windows):
            addresses = []

        for index, window in enumerate(windows):
            lat = self.value_before(latitudes, window.start())
            lon = self.value_before(longitudes, window.start())
            if not (lat and lon):
                continue

            name = Selector(text=window.group(1)).xpath("//h3/text()").get()

            item = Feature(
                ref="/".join([lat, lon, name or ""]),
                lat=lat,
                lon=lon,
                city=city,
                addr_full=addresses[index] if addresses else None,
            )
            if location_type == "atm":
                item["name"] = name
                apply_category(Categories.ATM, item)
            else:
                item["branch"] = name
                apply_category(Categories.BANK, item)

            yield item

    @staticmethod
    def value_before(positions: list[tuple[int, str]], offset: int) -> str | None:
        value = None
        for start, candidate in positions:
            if start >= offset:
                break
            value = candidate
        return value
