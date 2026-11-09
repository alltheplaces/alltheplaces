import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class EramFRSpider(Spider):
    name = "eram_fr"
    item_attributes = {"brand": "Éram", "brand_wikidata": "Q16684192"}
    allowed_domains = ["www.eram.fr"]
    # The full store list takes 10-30 s to render server side.
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    async def start(self) -> AsyncIterator[Any]:
        # Without the AJAX header the endpoint redirects to the homepage; without current_page it errors.
        yield Request(
            "https://www.eram.fr/store_locator/location/searchLocations?current_page=cms_page_view",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = response.css(".mw-sl__stores__list__item")
        if not stores:
            self.logger.warning("No store blocks found, the locator response format may have changed")
        for store in stores:
            days = {}
            for row in store.css(".mw-sl__stores__details__hours__table tr"):
                if day := sanitise_day(row.css("th::text").get(""), DAYS_FR):
                    hours = " ".join(row.css("td::text").getall())
                    days[day] = ("Fermé" in hours, re.findall(r"(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", hours))
            ranges = [r for _, day_ranges in days.values() for r in day_ranges]
            info = store.css(".mv-distance-info")
            ref = info.attrib.get("data-code")
            # 07xxx partner/overseas codes have placeholder coordinates; records whose only ranges
            # are empty (e.g. "01:00 - 01:00") have no real store data.
            if not ref or ref.startswith("07") or (ranges and all(start == end for start, end in ranges)):
                continue

            item = Feature()
            item["ref"] = ref
            item["lat"] = info.attrib.get("data-lat")
            item["lon"] = info.attrib.get("data-lng")
            name = " ".join(store.css(".mw-sl__store__info__name::text").get("").split())
            # Internal store-type suffixes: CC (shopping centre), BS, F.
            item["branch"] = re.sub(r"(\s+(CC|BS|F))+$", "", name.removeprefix("ERAM "))
            lines = [line.strip() for line in store.css("address.mw-sl__store__info::text").getall() if line.strip()]
            if lines and (m := re.match(r"(\d{5})\s+(.+)", lines[-1])):
                item["postcode"], item["city"] = m.groups()
                lines = lines[:-1]
            if street_address := clean_address(lines):
                item["street_address"] = street_address
            item["phone"] = store.css('a[href^="tel:"]::attr(href)').get()
            item["website"] = store.css(".mw-location-page-link a::attr(href)").get()

            oh = OpeningHours()
            for day, (closed, day_ranges) in days.items():
                if closed:
                    oh.set_closed(day)
                for open_time, close_time in day_ranges:
                    oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh

            yield item
