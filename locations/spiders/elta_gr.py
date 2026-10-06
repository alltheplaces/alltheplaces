import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class EltaGRSpider(Spider):
    name = "elta_gr"
    item_attributes = {"operator": "Ελληνικά Ταχυδρομεία", "operator_wikidata": "Q1275135"}
    allowed_domains = ["philotelismos.gr"]
    # The branch finder on elta.gr queries this endpoint; a 1,500 km radius from central Greece returns
    # every branch, agency and courier outlet in one response.
    start_urls = ["https://philotelismos.gr/closeBranch/el/38.5/23.5/1500/0"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for branch in response.json():
            if branch["active"] != "1":
                continue  # closed; rel_store points at the branch that replaced it
            name = branch["branches"].strip()
            kind = (re.search(r"\(([^)]+)\)\s*$", name) or [None, ""])[1]
            if "ΤΑΧΥΜΕΤΑΦΟΡ" in kind:
                continue  # ELTA Courier outlets ("ΠΡΑΚΤΟΡΕΙΟ/ΚΑΤΑΣΤΗΜΑ ΤΑΧΥΜΕΤΑΦΟΡΩΝ"), not post offices
            agency = "ΠΡΑΚΤΟΡΕΙ" in kind  # "ΤΑΧ. ΠΡΑΚΤΟΡΕΙΟ": a postal agency run by a third party
            if agency or "ΚΑΤΑΣΤΗΜΑ" in kind:
                name = name[: name.rindex("(")].strip()

            item = Feature()
            item["ref"] = branch["code"] or branch["id"]
            item["branch"] = name
            item["lat"], item["lon"] = branch["cordinates_lat"], branch["cordinates_long"]
            item["street"] = branch["street"]
            item["housenumber"] = branch["street_number"]
            item["postcode"] = branch["postcode"]
            item["city"] = branch["municipality"]
            item["phone"] = branch["telephone"]
            item["opening_hours"] = self.parse_hours(branch)
            if agency:
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
            else:
                apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def parse_hours(branch: dict) -> OpeningHours:
        # e.g. "07.30-14.45" or "09.30-15.00 &17.00-20.00"
        oh = OpeningHours()
        for days, text in (
            (DAYS[:5], branch.get("working_hours")),
            (["Sa"], branch.get("working_hours_saturday")),
            (["Su"], branch.get("working_hours_sunday")),
        ):
            for start, end in re.findall(r"(\d{1,2}[.:]\d{2})\s*-\s*(\d{1,2}[.:]\d{2})", text or ""):
                for day in days:
                    oh.add_range(day, start.replace(".", ":"), end.replace(".", ":"))
        return oh
