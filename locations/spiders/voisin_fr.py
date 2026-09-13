import re

import chompjs

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class VoisinFRSpider(JSONBlobSpider):
    name = "voisin_fr"
    item_attributes = {"brand": "Voisin", "brand_wikidata": "Q3562373", "name": "Voisin", "country": "FR"}
    start_urls = ["https://www.chocolat-voisin.com/boutiques/"]

    def extract_json(self, response):
        js = response.xpath('//script[contains(text(), "var locations")]/text()').get()
        js = js.split("var locations =", 1)[1].rsplit(";", 1)[0]
        return chompjs.parse_js_object(js)

    def pre_process_data(self, feature):
        # The website's own JS object has a copy/paste error where the
        # "Halles Paul Bocuse" store (dict key "lyon3_4") was given the same
        # inner "id" as the unrelated "Gare Part-Dieu" store ("lyon3_3"),
        # which would otherwise cause one of the two to be dropped as a
        # duplicate ref. The outer dict key is always unique, so prefer that.
        feature["id"] = feature.get("feature_id", feature.get("id"))

        # The website has a copy/paste error where the Paris 9 "Galeries
        # Lafayette" store is given the same coordinates as the Chambery
        # store. Drop the bogus coordinates rather than plotting this store
        # in the wrong city.
        if feature.get("id") == "paris_9":
            feature.pop("lat", None)
            feature.pop("lng", None)

        # Street is HTML with line breaks between a venue name (e.g. a
        # shopping centre) and the street address; flatten it to plain text.
        if street := feature.get("street"):
            street = re.sub(r"<br\s*/?>", ", ", street)
            street = re.sub(r"<[^>]+>", "", street)
            feature["street"] = street

        # City field is actually "<postcode> <city>" combined.
        if city := feature.get("city"):
            if m := re.match(r"^(\d{5})\s+(.+)$", city):
                feature["postcode"], feature["city"] = m.group(1), m.group(2)

    def post_process_item(self, item: Feature, response, feature: dict):
        # The source "name" field (e.g. "Lyon 1", "Paris 8ieme") is a branch
        # label, not a distinct store name; item_attributes["name"] backfills
        # the brand name once this is cleared.
        item["branch"] = item.pop("name", None)

        item["opening_hours"] = self.parse_hours(feature.get("horaires", {}))

        apply_category(Categories.SHOP_CHOCOLATE, item)

        yield item

    def parse_hours(self, horaires: dict) -> OpeningHours:
        oh = OpeningHours()
        for day_fr, periods in horaires.items():
            day = DAYS_FR.get(day_fr.title())
            if not day:
                continue
            for period in ("am", "pm"):
                times = periods.get(period)
                if not times:
                    continue
                open_time = self.parse_time(times.get("0"))
                close_time = self.parse_time(times.get("1"))
                if open_time and close_time:
                    oh.add_range(day, open_time, close_time)
        return oh

    @staticmethod
    def parse_time(value: str) -> str | None:
        if not value:
            return None
        if m := re.match(r"^(\d{1,2})h(\d{2})?$", value.strip()):
            hour, minute = int(m.group(1)), int(m.group(2) or 0)
            return f"{hour:02d}:{minute:02d}"
        return None
