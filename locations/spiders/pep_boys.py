import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

DIRECTORY = "https://www.pepboys.com/stores"
# The site is a Next.js application which streams the data its pages are built
# from as a series of JavaScript string chunks. Joined back together they hold
# the JSON behind the page.
CHUNK = re.compile(r'self\.__next_f\.push\(\[1,\s*("(?:[^"\\]|\\.)*")\s*\]\)')
# A city's own page, as the directory links it: /stores/al/birmingham
CITY = re.compile(r"^(?:https://www\.pepboys\.com)?/stores/[a-z]{2}/[^/]+/?$")
# A store's own page sits a step below that.
STORE = re.compile(r"^(?:https://www\.pepboys\.com)?/stores/[a-z]{2}/[^/]+/[^/]+/?$")
# "Birmingham, AL, 35213"
PLACE = re.compile(r"^\s*(?P<city>.+?),\s*(?P<state>[A-Z]{2}),\s*(?P<postcode>\d{5})")
# Every list of stores ends with a placeholder carrying no store at all.
NOTHING = "$undefined"


class PepBoysSpider(Spider):
    """The chain's directory reaches every store a city at a time.

    A city's page carries the whole of each of its stores - the number it is
    known by, its name, address, telephone, coordinates and the hours it keeps -
    so the stores' own pages are not fetched.

    The sitemap is not used. It lists 1,947 store pages where the directory
    counts 781 stores, naming 282 in California against the 108 the directory
    states, so most of what it offers is pages for stores that have closed.
    """

    name = "pep_boys"
    item_attributes = {"brand": "Pep Boys", "brand_wikidata": "Q3375007"}
    allowed_domains = ["www.pepboys.com"]
    start_urls = [DIRECTORY]
    # The site refuses a caller it does not take for a person, whatever it asks
    # for, so the requests are made from the proxy pool. Announcing ourselves a
    # crawler on top of that would undo it, the proxy saying as much itself, so
    # the ordinary browser agent is sent instead.
    requires_proxy = "US"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen: set[str] = set()

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for url in set(response.xpath('//a[contains(@href, "/stores/")]/@href').getall()):
            if CITY.match(url):
                yield response.follow(url, callback=self.parse_city)

    def parse_city(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # A store's own page is named after its street, which is how a store is
        # matched to it. The city's page also links its services, which are not
        # stores and match nothing.
        pages = {
            url.rstrip("/").rsplit("/", 1)[-1]: response.urljoin(url)
            for url in response.xpath('//a[contains(@href, "/stores/")]/@href').getall()
            if STORE.match(url)
        }

        for store in self.stores(response.text):
            if (ref := store.get("storeId")) in self.seen:
                continue
            self.seen.add(ref)

            item = Feature()
            item["ref"] = ref
            item["branch"] = self.spoken(store.get("displayName"))
            item["street_address"] = self.spoken(store.get("addressLine1"))
            item["phone"] = store.get("phone")
            if place := PLACE.match(store.get("cityStateZip") or ""):
                item["city"] = place["city"]
                item["state"] = place["state"]
                item["postcode"] = place["postcode"]
                # Thirty one of the stores are in Puerto Rico. Without the
                # country their telephone numbers do not survive validation.
                item["country"] = "PR" if place["state"] == "PR" else "US"
            else:
                self.logger.warning(f"Unparsed address {store.get('cityStateZip')!r} on {response.url}")

            if isinstance(point := store.get("geoPoint"), dict):
                item["lat"] = point.get("latitude")
                item["lon"] = point.get("longitude")

            item["opening_hours"] = self.parse_hours(store.get("openingHours"))
            item["website"] = pages.get(self.slug(store.get("addressLine1")))

            # The only picture a store carries is the chain's own photograph of
            # a shop interior, which every one of them repeats.
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item

    def stores(self, body: str) -> Iterable[dict]:
        """Walk the stores out of the data the page was built from."""
        payload = "".join(self.chunks(body))
        decoder = json.JSONDecoder()
        at = 0
        while (found := payload.find('"storeId"', at)) != -1:
            start = payload.rfind("{", 0, found)
            if start == -1:
                return
            try:
                store, length = decoder.raw_decode(payload[start:])
            except ValueError:
                at = found + 1
                continue
            at = start + length
            if isinstance(store, dict) and (store.get("storeId") or NOTHING) != NOTHING:
                yield store

    @staticmethod
    def chunks(body: str) -> Iterable[str]:
        for chunk in CHUNK.finditer(body):
            try:
                yield json.loads(chunk.group(1))
            except ValueError:
                continue

    def parse_hours(self, opening_hours: Any) -> OpeningHours:
        oh = OpeningHours()
        for rule in (opening_hours or {}).get("weekDayOpeningList") or []:
            if not (day := sanitise_day(rule.get("weekDay"))):
                continue
            if rule.get("closed"):
                oh.set_closed(day)
                continue
            opens = (rule.get("openingTime") or {}).get("formattedHour")
            closes = (rule.get("closingTime") or {}).get("formattedHour")
            if not opens or not closes:
                continue
            try:
                oh.add_range(day, opens, closes, time_format="%I:%M %p")
            except ValueError:
                self.logger.warning(f"Unparsed hours {opens!r} to {closes!r} on {day}")
        return oh

    @staticmethod
    def slug(value: str | None) -> str:
        return re.sub(r"[^a-z0-9]+", "-", (value or "").casefold()).strip("-")

    @staticmethod
    def spoken(value: str | None) -> str | None:
        """Take the shouting out of a name the site writes in capitals.

        Most are published in capitals, a few are not, and those are left as
        they are so that a building's initials are not turned into a word.
        """
        if not (value := re.sub(r"\s+", " ", value or "").strip()):
            return None
        if value != value.upper():
            return value
        words = []
        for word in value.split():
            if any(character.isdigit() for character in word):
                words.append(word)
            else:
                # Each run of letters is capitalised on its own, so that a name
                # such as O'BRIEN does not come out as O'brien.
                words.append(re.sub(r"[^\W\d_]+", lambda run: run.group().capitalize(), word))
        return " ".join(words) or None
