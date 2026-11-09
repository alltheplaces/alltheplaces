import re
from collections import Counter, defaultdict
from typing import Any, Iterable

from chompjs import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.state_clean_up import STATES
from locations.react_server_components import parse_rsc

DIRECTORY = "https://www.bubbakoos.com/location-directory"
# A restaurant that has yet to open says so against this field.
OPEN = "open"
# Most of the restaurants are named for their town alone, but some append the
# chain's name, spelled three ways between them.
CHAIN = re.compile(r"\s*-?\s*Bubbakoo['’]s Burrito['’]?s\s*$", re.IGNORECASE)


class BubbakoosBurritosUSSpider(JSONBlobSpider):
    name = "bubbakoos_burritos_us"
    item_attributes = {"brand": "Bubbakoo's Burritos", "brand_wikidata": "Q114619751"}
    start_urls = [DIRECTORY]

    def extract_json(self, response: Response) -> list[dict]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for _, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        locations = {}
        self.find_locations(dict(parse_rsc(rsc.encode())), locations)
        return list(locations.values())

    def find_locations(self, node: Any, locations: dict) -> None:
        if isinstance(node, dict):
            if "latitude" in node and "id" in node:
                locations[node["id"]] = node
            for value in node.values():
                self.find_locations(value, locations)
        elif isinstance(node, list):
            for value in node:
                self.find_locations(value, locations)

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        if (status := feature.get("location_status")) != OPEN:
            self.logger.info(f"{feature.get('name')} is {status}, so it is not published")
            return

        # The locator names each restaurant for its town, which is its branch
        # rather than a name of its own.
        item.pop("name", None)
        item["branch"] = self.branch(feature)
        item["street_address"] = item.pop("addr_full")
        item["website"] = self.location_page(feature)

        # One town is written in lower case throughout.
        if (city := item.get("city")) and city == city.lower():
            item["city"] = city.title()

        item["opening_hours"] = self.parse_hours(feature)

        # The remaining flags the locator carries - dine in, curbside, drive
        # through - describe what its ordering service offers rather than what
        # the restaurant has, every one of them denying a drive through, so
        # they are not read as facts about the place.
        apply_yes_no(Extras.DELIVERY, item, feature.get("supportsDelivery"))
        apply_category(Categories.FAST_FOOD, item)

        yield item

    @staticmethod
    def branch(feature: dict) -> str:
        """Return the name of the restaurant's own town.

        A few of them end in the state they stand in, which the address states
        already.
        """
        branch = CHAIN.sub("", feature.get("name") or "").strip(" -")
        if state := feature.get("state"):
            branch = re.sub(rf"[\s,]+{re.escape(state)}$", "", branch)
        return branch.strip(" -")

    @staticmethod
    def location_page(feature: dict) -> str | None:
        """Return the page the site gives the restaurant.

        Pages are addressed by state and town, so the four towns holding more
        than one restaurant give those restaurants a page between them.
        """
        state = STATES["US"].get(feature.get("state") or "")
        town = BubbakoosBurritosUSSpider.slug(feature.get("city"))
        if not state or not town:
            return None
        return f"{DIRECTORY}/{BubbakoosBurritosUSSpider.slug(state['name'])}/{town}"

    @staticmethod
    def slug(value: str | None) -> str:
        return re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")

    def parse_hours(self, feature: dict) -> OpeningHours:
        """Read the hours out of the month of dates the locator states.

        The hours are given as a calendar of the coming month rather than as a
        week, so each weekday is stated four or five times over. A day shut
        early for a holiday falls inside that month and is stated once against
        the four that give the hours the restaurant usually keeps, so each
        weekday is taken as the greater number of its dates agree.
        """
        stated: dict[str, Counter] = defaultdict(Counter)
        for calendar in feature.get("calendars") or []:
            if calendar.get("type") != "business":
                continue
            dates: dict[str, set] = defaultdict(set)
            weekdays: dict[str, str] = {}
            for rule in calendar.get("ranges") or []:
                date, opens = rule["start"].split(" ")
                dates[date].add((opens, rule["end"].split(" ")[1]))
                weekdays[date] = rule["weekday"]
            for date, ranges in dates.items():
                stated[weekdays[date]][tuple(sorted(ranges))] += 1

        oh = OpeningHours()
        for weekday, dayparts in stated.items():
            usual, _ = dayparts.most_common(1)[0]
            for opens, closes in usual:
                oh.add_range(weekday, opens, closes)
        return oh
