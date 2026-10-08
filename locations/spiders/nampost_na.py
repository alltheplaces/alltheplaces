import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature

OPERATOR = {"operator": "NamPost", "operator_wikidata": "Q1509637"}


class NampostNASpider(Spider):
    name = "nampost_na"
    allowed_domains = ["www.nampost.com.na"]
    # The page embeds every office and agent as a JS object: "var items = {...};"
    start_urls = ["https://www.nampost.com.na/contact-us/post-offices"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        start = response.text.find("var items = {")
        items = json.JSONDecoder().raw_decode(response.text, start + len("var items = "))[0]
        for office in items.values():
            if office.get("deleted_at"):
                continue
            # Newer entries without a real position default to (-30, 24), which is in South Africa.
            if float(office["latitude"]) == -30 and float(office["longitude"]) == 24:
                self.crawler.stats.inc_value("atp/nampost_na/placeholder_coordinates")
                continue
            item = Feature()
            item["ref"] = str(office["id"])
            item["lat"], item["lon"] = office["latitude"], office["longitude"]
            item["street_address"] = (office.get("address") or "").strip(" .") or None
            item["postcode"] = office.get("post_code")
            item["city"] = (office.get("city") or {}).get("title")
            item["phone"] = office.get("telephone") or office.get("cellphone")
            item["email"] = office.get("email")
            item["opening_hours"] = self.parse_hours(office.get("weekdays"), office.get("saturdays"))
            name = office["name"].strip()
            # "type" is the role of the person in charge; "Agent" means a counter run by a third party.
            if office.get("type") == "Agent":
                item["name"] = name
                item["extras"]["post_office"] = "post_partner"
                item["extras"]["post_office:brand"] = OPERATOR["operator"]
                item["extras"]["post_office:brand:wikidata"] = OPERATOR["operator_wikidata"]
                apply_category(Categories.GENERIC_POI, item)
            else:
                item.update(OPERATOR)
                item["branch"] = re.sub(r"\s*(main\s+)?post\s+office$", "", name, flags=re.I)
                apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def parse_hours(weekdays: str | None, saturdays: str | None) -> OpeningHours:
        oh = OpeningHours()

        def times(text: str) -> list[str]:
            return [f"{h.zfill(2)}:{m}" for h, m in re.findall(r"(\d{1,2})[:h](\d{2})", text or "")]

        if len(weekday := times(weekdays)) == 2:
            oh.add_days_range(DAYS_WEEKDAY, *weekday)
        saturday = times(saturdays)
        if len(saturday) == 1 and len(weekday) == 2:
            # Saturdays are usually given as the closing time only ("12:00"); offices open as on weekdays.
            saturday = [weekday[0], saturday[0]]
        if len(saturday) == 2:
            oh.add_range("Sa", *saturday)
        oh.set_closed("Su")
        return oh
