from collections import defaultdict
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY
from locations.items import Feature
from locations.storefinders.drupal_json_api import parse_address_field, parse_office_hours


class StartPeopleFRSpider(Spider):
    name = "start_people_fr"
    item_attributes = {"brand": "Start People", "brand_wikidata": "Q2646530"}
    allowed_domains = ["www.startpeople.fr"]
    start_urls = ["https://www.startpeople.fr/nos-agences/carte"]

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[JsonRequest]:
        # The map page lists every agency but only says whether each is open right now;
        # Drupal's REST resource for the node has the weekly hours and the email.
        # Some agencies are listed twice under the same name, as a stale node and a live one.
        urls_by_name = defaultdict(list)
        for location in response.css(".geolocation-location"):
            if url := location.css(".agency-name a::attr(href)").get():
                urls_by_name[location.css(".location-title::text").get()].append(
                    response.urljoin(url) + "?_format=json"
                )
        # One request per agency name; its other nodes, if any, are fetched in turn.
        for urls in urls_by_name.values():
            yield JsonRequest(urls[0], callback=self.parse_agency, cb_kwargs={"other_urls": urls[1:]})

    def parse_agency(
        self, response: TextResponse, other_urls: list[str], latest: dict | None = None
    ) -> Iterable[JsonRequest | Feature]:
        # Keep the most recently changed node: the site's sync only updates the live one.
        agency = response.json()
        if latest and latest["changed"][0]["value"] > agency["changed"][0]["value"]:
            agency = latest
        # Another node has the same name: fetch it and carry the best one so far.
        if other_urls:
            yield JsonRequest(
                other_urls[0], callback=self.parse_agency, cb_kwargs={"other_urls": other_urls[1:], "latest": agency}
            )
            return

        # All nodes of this agency have been compared.
        slots = agency.get("field_opening_hours") or []
        agency = {key: value[0] for key, value in agency.items() if value}
        item = Feature()
        item["ref"] = agency["nid"]["value"]
        item["website"] = response.urljoin(agency["path"]["alias"])
        item["branch"] = agency.get("title", {}).get("value", "").removeprefix("Start People ")
        parse_address_field(agency.get("field_address"), item)
        if geo := agency.get("field_geoloc"):
            item["lat"], item["lon"] = geo.get("lat"), geo.get("lng")
        item["phone"] = agency.get("field_phone", {}).get("value")
        item["email"] = agency.get("field_email", {}).get("value")

        if any(slot.get("comment") for slot in slots):
            # Some slots are by appointment ("Sur RDV"), with or without times: keep the
            # comment, which OpeningHours cannot carry.
            days_by_rule = defaultdict(list)
            for slot in slots:
                rule = ""
                if slot.get("all_day"):
                    rule = "00:00-24:00"
                elif slot.get("starthours") is not None and slot.get("endhours") is not None:
                    rule = "{:02}:{:02}-{:02}:{:02}".format(
                        *divmod(int(slot["starthours"]), 100), *divmod(int(slot["endhours"]), 100)
                    )
                if slot.get("comment"):
                    rule = '{} "{}"'.format(rule, slot["comment"].replace('"', "")).strip()
                if rule and slot.get("day") is not None:
                    days_by_rule[rule].append(DAYS_FROM_SUNDAY[int(slot["day"])])
            item["opening_hours"] = ", ".join(
                "{} {}".format(",".join(days), rule) for rule, days in days_by_rule.items()
            )
        else:
            item["opening_hours"] = parse_office_hours(slots)

        apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
        yield item
