import html
import json
import re
from datetime import datetime
from typing import Any, Iterable

import pycountry
from scrapy import Spider
from scrapy.http import Response
from scrapy.selector import Selector

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours, day_range, sanitise_day
from locations.items import Feature

DAY = r"Sun(?:n)?(?:day)?|Mon(?:day)?|Tues?(?:day)?|Wed(?:nesday)?|Thur?s?(?:day)?|Fri(?:day)?|Sat(?:urday)?"
TIME = r"\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?"
JOIN = r"[-–]|&|and|to|,"
# "Sun – Thurs: 11am – 9pm", "Fri & Sat: 11am-10pm", "Open Daily: 11am-9pm",
# "Fri – Sat: Dine-In Hours 11am – 11pm"
RANGE = re.compile(
    rf"^(?:(?P<daily>open\s+daily|daily|every\s*day)"
    rf"|(?P<days>(?:{DAY})(?:\s*(?P<join>{JOIN})\s*(?:{DAY}))*))"
    rf"\s*[:\-–]?\s*(?:[\w/-]+(?:\s+[\w/-]+)?\s+hours\s+)?"
    rf"(?P<opens>{TIME})\s*(?:[-–]|to)\s*(?P<closes>{TIME})",
    re.IGNORECASE,
)
CLOSED = re.compile(rf"^(?P<days>(?:{DAY})(?:\s*(?:{JOIN})\s*(?:{DAY}))*)\s*[:\-–]?\s*closed\b", re.IGNORECASE)
# Many restaurants follow their own hours with a holiday or bar schedule, which
# describes a different day or a different counter and is not what they open for.
OTHER_HOURS = re.compile(r"(holiday|bar|delivery|kitchen|brunch|happy)\s*hours?|^holiday", re.IGNORECASE)
# The five restaurants on the other site state their hours as JSON instead.
STORE_HOURS = re.compile(r'"store_hours"\s*:\s*(\{.*?\}\s*\})')
US_STATES = {}
for subdivision in pycountry.subdivisions.get(country_code="US"):
    US_STATES[subdivision.name.casefold()] = (code := subdivision.code.split("-")[1])
    US_STATES[code.casefold()] = code
# Where an address runs its street and city together, the city begins after the
# last street type or unit number.
STREET_TAIL = re.compile(
    r"\b(?:st|street|ave|avenue|blvd|boulevard|rd|road|dr|drive|ln|lane|way|pkwy|parkway|hwy|highway|ct|court"
    r"|cir|circle|pl|place|ter|terrace|trl|trail|pike|plaza|mall|center|centre|row|sq|square)\b\.*"
    r"|#\s*\d+\w*|\b(?:ste|suite|unit|apt|bldg|building|space|spc)\b\.?\s*[\w&#-]+|\([^)]*\)",
    re.IGNORECASE,
)


class MyrosatisUSSpider(Spider):
    name = "myrosatis_us"
    item_attributes = {"brand": "Rosati's", "brand_wikidata": "Q65052579"}
    start_urls = ["https://myrosatis.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        # The locator lists nothing until a state is chosen, so each state is asked for.
        for url in response.xpath("//option[@data-url]/@data-url").getall():
            yield response.follow(url, callback=self.parse_state)

    def parse_state(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for card in response.xpath('//article[contains(@class, "article-location")]'):
            # Most of the links on a card open an ordering site; one is the restaurant's
            # own page. That link is the only stable reference the locator publishes, and
            # it is trusted over the page it leads to: one restaurant's link redirects to
            # a different, unopened restaurant's page.
            url = card.xpath('.//a[contains(@href, "myrosatis")][not(contains(@href, "order."))]/@href').re_first(
                r"^([^#?]+)"
            )
            if not url:
                self.logger.warning(f"No location link on card {card.xpath('normalize-space(.//h3)').get()!r}")
                continue

            item = Feature()
            item["ref"] = url.rstrip("/").rsplit("/", 1)[-1]
            item["website"] = url
            # The cards name their restaurants in capitals.
            item["branch"] = self.titlecase(card.xpath("normalize-space(.//h3)").get(""))
            item["lat"] = card.xpath("@data-lat").get()
            item["lon"] = card.xpath("@data-lng").get()

            details = self.card_details(card)
            self.apply_address(item, " ".join(details.get("address", [])))
            item["phone"] = self.phone(details.get("phone", []))

            # The locator also flags which restaurants have a dining room, a sports bar
            # or a catering service, but the brand is categorised as fast food both by
            # the name suggestion index and by the spider for the chain's other site.
            categories = (card.xpath("@data-category").get() or "").split(",")
            apply_category(Categories.FAST_FOOD, item)
            apply_yes_no("takeaway", item, "carryoutdelivery" in categories)
            apply_yes_no("delivery", item, "carryoutdelivery" in categories)
            item["extras"]["cuisine"] = "pizza"

            # Only one day's status is shown on a card, so the restaurant's own page is
            # read for the week it keeps.
            yield response.follow(url, callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        if lines := self.labelled(response, "hours"):
            item["opening_hours"] = self.hours(lines)
        elif store_hours := STORE_HOURS.search(response.text):
            item["opening_hours"] = self.json_hours(store_hours.group(1))

        # The restaurants on the other site describe themselves differently, and a few
        # cards state no address or phone of their own.
        if not item.get("street_address"):
            self.apply_address(item, self.block_address(response))
        if not item.get("phone"):
            item["phone"] = self.phone(self.labelled(response, "phone"))
        yield item

    # Hours ----------------------------------------------------------------

    def hours(self, lines: list[str]) -> OpeningHours:
        oh = OpeningHours()
        for line in lines:
            if OTHER_HOURS.search(line):
                break
            if match := RANGE.match(line):
                closes = self.normalise(match["closes"])
                if closes == "00:00":
                    # These kitchens close at midnight rather than opening for a minute.
                    closes = "24:00"
                days = DAYS if match["daily"] else self.days(match["days"], match["join"])
                if not days:
                    self.logger.warning(f"Unparsed days: {line!r}")
                    continue
                for day in days:
                    oh.add_range(day, self.normalise(match["opens"]), closes)
            elif match := CLOSED.match(line):
                for day in self.days(match["days"], None):
                    oh.set_closed(day)
        return oh

    def json_hours(self, blob: str) -> OpeningHours:
        oh = OpeningHours()
        try:
            store_hours = json.loads(blob.replace("\\/", "/"))
        except json.JSONDecodeError:
            self.logger.warning(f"Unparsed hours: {blob!r}")
            return oh
        for name, times in store_hours.items():
            if not (day := sanitise_day(name)) or not isinstance(times, dict):
                continue
            if (opens := times.get("open")) and (closes := times.get("close")):
                oh.add_range(day, opens, "24:00" if closes == "00:00" else closes)
        return oh

    @staticmethod
    def days(labels: str, joiner: str | None) -> list[str]:
        days = []
        for label in re.split(rf"\s*(?:{JOIN})\s*", labels):
            # One restaurant misspells a day by doubling its last letter.
            if day := sanitise_day(label) or sanitise_day(re.sub(r"(.)\1+$", r"\1", label)):
                days.append(day)
        if len(days) == 2 and (joiner or "").strip().casefold() in ("-", "–", "to"):
            days = day_range(*days)
        return days

    @staticmethod
    def normalise(time: str) -> str:
        time = re.sub(r"[\s.]", "", time).upper()
        return datetime.strptime(time, "%I:%M%p" if ":" in time else "%I%p").strftime("%H:%M")

    # Addresses ------------------------------------------------------------

    def apply_address(self, item: Feature, address: str) -> None:
        if not address:
            return
        if not (parsed := self.parse_address(address)):
            self.logger.warning(f"Unparsed address: {address!r}")
            return
        item["street_address"], item["city"], item["state"], item["postcode"] = parsed
        if not item["city"]:
            self.logger.warning(f"No city in address: {address!r}")

    @staticmethod
    def parse_address(address: str) -> tuple[str, str | None, str, str | None] | None:
        """Parse "4206 E. Chandler Blvd., #34, Phoenix, AZ 85048" and the shapes beside it.

        The commas are unreliable: some addresses omit the one before the city or
        before the state, some put one after the state, and some name the state in
        full. One address states no postcode at all.
        """
        address = re.sub(r"\s+", " ", html.unescape(address or "")).strip()
        # One address notes its cross streets after the postcode.
        address = re.sub(r"\s*\((?:[^()]*&[^()]*)\)\s*$", "", address)
        address = re.sub(r",(?=\S)", ", ", address).strip(" ,")

        postcode = None
        if match := re.search(r"[,\s]\s*([A-Za-z]{2}|[A-Za-z]{4,20})\.?,?\s*(\d{5})(?:-\d{4})?$", address):
            state = US_STATES.get(match.group(1).casefold())
            postcode = match.group(2)
        elif match := re.search(r"[,\s]\s*([A-Za-z]{2}|[A-Za-z]{4,20})\.?$", address):
            state = US_STATES.get(match.group(1).casefold())
        else:
            return None
        if not state:
            return None

        head = address[: match.start()].strip(" ,.")
        street, city = head, None
        if "," in head:
            street, _, city = head.rpartition(",")
        # A unit can follow the last comma, leaving the city run on from it, and a
        # street with no comma at all runs straight into its city.
        probe = city if city is not None else head
        ends = [tail.end() for tail in STREET_TAIL.finditer(probe)]
        if ends and ends[-1] < len(probe) - 1:
            extra, rest = probe[: ends[-1]], probe[ends[-1] :]
            if city is None:
                street, city = extra, rest
            elif re.search(r"\w", extra):
                street, city = f"{street}, {extra}", rest
        return street.strip(" ,"), (city or "").strip(" ,") or None, state, postcode

    @staticmethod
    def block_address(response: Response) -> str:
        """Return the address beside the directions link used on the other site."""
        block = response.xpath(
            '//*[a[contains(translate(., "GETDIRECTIONS", "getdirections"), "get directions")]]'
            '[not(.//*[a[contains(translate(., "GETDIRECTIONS", "getdirections"), "get directions")]])]'
        )
        lines = [re.sub(r"\s+", " ", line).strip() for line in block.xpath(".//text()").getall()]
        lines = [line for line in lines if line and "get directions" not in line.casefold()]
        # The street is stated above "City, ST 12345".
        for index, line in enumerate(lines):
            if re.search(r",\s*[A-Z]{2}\s+\d{5}", line) and index:
                return f"{lines[index - 1]}, {line}"
        return ""

    # Shared ---------------------------------------------------------------

    @staticmethod
    def phone(values: list[str]) -> str | None:
        for value in values:
            if re.search(r"\d{3}\D*\d{4}", value):
                return value.strip()
        return None

    @staticmethod
    def titlecase(name: str) -> str | None:
        # One restaurant repeats the brand after its own name.
        name = re.sub(r"\s*[-–—]\s*Rosati['’]s(?:\s+Pizza)?\s*$", "", name or "", flags=re.IGNORECASE)
        name = re.sub(r"[^\W\d_]+(?:['’][^\W\d_]+)?", lambda word: word.group().capitalize(), name)
        # "116Th" reads as an ordinal rather than a word.
        return re.sub(r"(?<=\d)(St|Nd|Rd|Th)\b", lambda suffix: suffix.group().lower(), name).strip() or None

    @staticmethod
    def card_details(card: Selector) -> dict[str, list[str]]:
        """Return a card's labelled lines, keyed by their label."""
        return MyrosatisUSSpider.group(card.xpath('.//div[contains(@class, "article__body")]//text()').getall())

    @staticmethod
    def labelled(response: Response, label: str) -> list[str]:
        """Return the lines of a location page's labelled block."""
        for block in response.xpath("//li[p/strong]"):
            heading = (block.xpath("normalize-space(p/strong)").get("") or "").rstrip(":").casefold()
            if heading != label:
                continue
            lines = []
            for paragraph in block.xpath("p[position()>1]"):
                # A block states one schedule per line, which is broken by <br> as
                # often as by a new paragraph, and labels some lines in their own tag.
                for part in re.split(r"<br[^>]*>", paragraph.get()):
                    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", part))).strip().strip("*")
                    if text:
                        lines.append(text)
            return lines
        return []

    @staticmethod
    def group(texts: list[str]) -> dict[str, list[str]]:
        labels = ("Address", "Phone", "Hours", "Open Today")
        grouped: dict[str, list[str]] = {}
        current = None
        for text in texts:
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue
            if text in labels:
                current = text.casefold()
            elif current:
                grouped.setdefault(current, []).append(text)
        return grouped
