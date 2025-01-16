import re

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import CLOSED_IT, DAYS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class InpostITSpider(JSONBlobSpider):
    name = "inpost_it"
    allowed_domains = ["inpost.it"]
    start_urls = []  # ["https://inpost.it/sites/default/files/points.json"]
    locations_key = "items"
    requires_proxy = True

    operator = {"operator": "InPost", "operator_wikidata": "Q3182097"}
    brand_locker = {"brand": "InPost", "brand_wikidata": "Q3182097"}
    brand_partner = {"post_office:brand": "InPost", "post_office:brand:wikidata": "Q3182097"}

    def start_requests(self):
        for domain in self.allowed_domains:
            self.start_urls.append(f"https://{domain}/sites/default/files/points.json")
        yield from super().start_requests()

    def pre_process_data(self, v):
        # this mapping comes from "load" js function in inpost webpage
        location = {
            "position": {"lat": v["l"]["a"], "lng": v["l"]["o"]},
            "street": v["e"],
            "house-number": v["b"],
            "province": v["r"],
            "post_code": v["o"],
            "city": v["c"],
            "type": v["t"],
            "name": v["d"],  # originally, location_description
            "hours": v["h"],
            "payment": v["p"],
            "ref": v["n"],  # originally, name
            "status": v["s"],
            "apm_doubled": v["m"],
        }
        v.clear()
        v.update(location)
        v["active"] = int(v["status"]) == 1
        v["category"] = Categories.PARCEL_LOCKER if int(v["type"]) == 1 else Categories.POST_PARTNER

    def post_process_item(self, item, response, location):
        if not location["active"]:
            return None

        if hours := location["hours"]:
            if hours == "24/7":
                item["opening_hours"] = hours
            else:
                item["opening_hours"] = OpeningHours()
                self.parse_hours(item["opening_hours"], hours)

        apply_category(location["category"], item)
        apply_yes_no(Extras.PARCEL_MAIL_IN, item, True)
        apply_yes_no(Extras.PARCEL_PICKUP, item, True)
        self.set_brand(item, location)
        item["website"] = response.urljoin("/" + self.parse_slug(item, location))
        self.clean_address(item, location)
        if location["category"] == Categories.PARCEL_LOCKER:
            item.update(self.operator)
            yield from self.post_process_locker(item, location)
        else:
            item["extras"]["ref:inpost"] = item["ref"]
            yield from self.post_process_partner(item, location)

    def parse_hours(self, oh, hours):
        oh.add_ranges_from_string(
            hours,
            days=DAYS_IT,
            named_day_ranges=NAMED_DAY_RANGES_IT,
            named_times=NAMED_TIMES_IT,
            closed=CLOSED_IT,
        )

    def set_brand(self, item, location):
        if location["category"] == Categories.PARCEL_LOCKER:
            item.update(self.brand_locker)
        else:
            item["extras"].update(self.brand_partner)

    def clean_address(self, item, location):
        item["addr_full"] = [
            f'{item["street"] or ""} {item["housenumber"] or ""}',
            f'{item["postcode"] or ""} {item["city"] or ""}',
        ]
        if item["housenumber"]:
            item["housenumber"] = item["housenumber"].lower()

    def post_process_locker(self, item, location):
        yield item

    def post_process_partner(self, item, location):
        item["name"] = item["name"].removeprefix("presso").strip()
        yield item

    def slug_parts(self, item, location):
        if location["category"] == Categories.PARCEL_LOCKER:
            return ["locker", item["city"], item["ref"], item["street"]]
        else:
            return ["punto-ritiro", item["ref"], item["city"], item["street"]]

    def parse_slug(self, item, location):
        slug_parts = self.slug_parts(item, location)
        slug = "-".join(map(lambda x: x.lower().strip(), slug_parts))
        slug = re.sub(r"[·/_:; ]", "-", slug)
        slug = re.sub(r"[^a-z0-9-]", "", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug
