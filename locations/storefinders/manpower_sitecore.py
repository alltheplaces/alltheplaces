import json
import re
from collections import Counter
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ManpowerSitecoreSpider(Spider):
    """
    Manpower's national sites built on Sitecore JSS embed every branch of the country in the state of their branch
    locator page. This class contains their common spider code.

    `hours_kwargs` are the language tables passed to `OpeningHours.add_ranges_from_string`.
    """

    item_attributes = {"brand": "Manpower", "brand_wikidata": "Q1472539"}
    hours_kwargs: dict[str, Any] = {}

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        state = json.loads(response.xpath('//script[@id="__JSS_STATE__"]/text()').get(""))
        locations = [
            {key: field.get("value") for key, field in location["fields"].items() if isinstance(field, dict)}
            | {"id": location["id"]}
            for component in state["sitecore"]["route"]["placeholders"]["jss-main"]
            if component.get("componentName") == "LocationsFinder"
            for location in component["fields"]["items"]
        ]
        for location in locations:
            # Some sites give the branch email in the address instead.
            location["email"] = (location.get("email") or "").strip() or next(
                iter(re.findall(r"\S+@\S+", location.get("address") or "")), ""
            )
        # A phone number or email listed on several branches is a call centre, a regional office or a person.
        phones = Counter(re.sub(r"\D", "", location.get("phone") or "") for location in locations)
        emails = Counter(location["email"].lower() for location in locations)

        for location in locations:
            # Client sites, head offices and teams are listed but hidden from the locator.
            if location.get("VisibleInBranchLocator") is False:
                continue
            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = re.sub(r"^.*\bManpower (?:di )?", "", location["title"].strip())
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longtitude")
            if href := (location.get("ViewDetailsUrl") or {}).get("href"):
                item["website"] = response.urljoin(href)

            address = location.get("address") or ""
            lines = [line.strip(" ,") for line in address.splitlines() if line.strip(" ,")]
            postcode = (location.get("zipcode") or "").strip()
            if location.get("city"):
                item["street_address"] = merge_address_lines([location.get("address1"), location.get("address2")])
                item["city"] = location["city"]
                item["state"] = location.get("state")
                item["postcode"] = postcode
                if item["state"] == "Puerto Rico":
                    item["country"] = "PR"
            elif (match := re.match(r"(\d[\d -]*\d)\W*(.*)", postcode)) and lines:
                # The postcode field sometimes carries the city as well.
                item["street_address"] = lines[0]
                item["postcode"] = match.group(1)
                item["city"] = match.group(2) or None
            else:
                item["addr_full"] = merge_address_lines(lines)

            if (phone := location.get("phone")) and phones[re.sub(r"\D", "", phone)] == 1:
                item["phone"] = phone
            email = location["email"]
            if emails[email.lower()] == 1 and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                item["email"] = email

            # Without days in the text nothing is parsed, which is what we want.
            hours = re.sub(r"\bkl (\d\d)-(\d\d)\b", r"\1:00-\2:00", location.get("hours") or "")
            oh = OpeningHours()
            try:
                oh.add_ranges_from_string(hours.replace(" t/m ", " - ").replace(" & ", " - "), **self.hours_kwargs)
            except (IndexError, KeyError, ValueError):
                pass
            if any(oh.day_hours.values()):
                item["opening_hours"] = oh

            apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
            yield item
