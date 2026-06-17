import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SofiaUrbanMobilityCenterBGSpider(Spider):
    """Spider for Sofia Urban Mobility Center (Център за градска мобилност) ticket offices.
    Closes #5846
    """

    name = "sofia_urban_mobility_center_bg"
    item_attributes = {
        "brand": "Център за градска мобилност",
        "brand_wikidata": "Q7553668",
    }
    start_urls = ["https://webportal.sofiatraffic.bg/bg/contacts"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # The page is a React SPA — the location data lives in a versioned JS bundle
        bundle_path = response.xpath('//script[@type="module"]/@src').get()
        if not bundle_path:
            self.logger.error("Could not find JS bundle link")
            return
        yield response.follow(bundle_path, callback=self.parse_bundle)

    def parse_bundle(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        js = response.text

        # Find the Fv={...} object containing all office locations
        idx = js.find("const Fv={")
        if idx < 0:
            self.logger.error("Could not find locations object in JS bundle")
            return

        start = idx + len("const Fv=")
        depth = 0
        end = start
        for i, c in enumerate(js[start:], start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        raw = js[start:end]

        # Parse each location entry with regex — the JS uses unquoted numeric keys
        # and single-quoted strings which aren't valid JSON
        for m in re.finditer(
            r"\d+:\{name:\{bg:'(.*?)',en:'(.*?)'\},id:(\d+).*?"
            r"workingHours:\{weekday:\"(.*?)\",saturday:\"(.*?)\",sunday:\"(.*?)\".*?"
            r"location:\{lat:([\d.]+),lng:([\d.]+)\}",
            raw,
            re.DOTALL,
        ):
            name_bg, name_en, ref, weekday, saturday, sunday, lat, lng = m.groups()

            item = Feature()
            item["ref"] = ref
            item["name"] = name_en or name_bg
            item["lat"] = float(lat)
            item["lon"] = float(lng)

            oh = OpeningHours()
            if weekday:
                for day in ["Mo", "Tu", "We", "Th", "Fr"]:
                    oh.add_range(day, *weekday.split("-"))
            if saturday:
                oh.add_range("Sa", *saturday.split("-"))
            if sunday:
                oh.add_range("Su", *sunday.split("-"))
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_TICKET, item)
            yield item
