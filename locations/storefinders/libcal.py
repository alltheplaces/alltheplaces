import re
from collections import Counter
from functools import cached_property
from typing import Any, AsyncIterator, Iterable
from urllib.parse import unquote

import phonenumbers
from scrapy import Selector, Spider
from scrapy.http import JsonRequest, Request, TextResponse

from locations.categories import Categories, Extras, apply_category
from locations.country_utils import CountryUtils
from locations.hours import DAYS_FULL, NAMED_TIMES_EN, OpeningHours
from locations.items import Feature

EMAIL_REGEX = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Split a line of text before each label, so that each number can be
# classified by the label before it. Combined labels such as "Tel/Fax:" or
# "Phone or text:" are not split, so they are classified by their first word.
# "or" only joins labels directly after a label, as in "(415) 258-4656 or
# Text: (415) 855-1597" it separates two numbers.
LABEL_SPLIT_REGEX = re.compile(
    r"(?i)(?<![/&])(?<![/&]\s)(?<!phone\sor\s)(?<!\btel\sor\s)(?=\b(?:fax|phone|telephone|tel|text|sms)\b)"
)
FAX_LABEL_REGEX = re.compile(r"\bfax\b", re.IGNORECASE)
SMS_LABEL_REGEX = re.compile(r"\b(?:text|sms)\b", re.IGNORECASE)
# Several numbers in one tel: link, e.g. "(714)526-7728or(562)694-0078".
PHONE_OR_REGEX = re.compile(r"\s*(?:\bor\b|(?<=\d)or(?=[\d(+]))\s*")
BLOCK_TAG_REGEX = re.compile(r"<\s*(?:br|/p|/div|/li|/h\d|/td|/tr)\b[^>]*>", re.IGNORECASE)
NAMED_TIMES = NAMED_TIMES_EN | {"Noon": ["12:00PM", "12:00"]}


def label_type(text: str) -> str | None:
    """Return "fax", "sms", "phone" or None for text that may start with a label."""
    text = text.lstrip(" \t:-#(")
    if FAX_LABEL_REGEX.match(text):
        return "fax"
    if SMS_LABEL_REGEX.match(text):
        return "sms"
    if re.match(r"(?i)(?:phone|telephone|tel)\b", text):
        return "phone"
    return None


class LibCalSpider(Spider):
    """
    LibCal is Springshare's calendar, room booking and hours platform for
    libraries. Its public hours API lists a tenant's locations with hours
    for the coming weeks.
    https://springshare.com/libcal/

    To use, specify:
      - `libcal_host`: e.g. "ocpl.libcal.com"
      - `libcal_iid`: the institution ID, found in the page source of
        https://<libcal_host>/hours (e.g. `iid: 6287`)
      - `country`: optional, for finding phone numbers in free text if the
        spider name has no country suffix

    LibCal rarely has addresses or coordinates, so these usually need to be
    taken from the branch web page: have `parse_item` yield a request for
    `item["website"]` carrying the item in `cb_kwargs`.

    Only "library" locations are returned; "department" locations inside a
    library are skipped. The location name is stored as `branch`, and
    subclasses should set `name`. Override `parse_item(item, location)` to
    modify or skip locations (e.g. bookmobiles, offices, virtual services).

    A location closed every day gets "Mo-Su closed", the ATP convention for a
    temporary closure; mark permanently closed locations with `set_closed`.
    """

    dataset_attributes: dict = {"source": "api", "api": "libcal.com"}
    libcal_host: str
    libcal_iid: int | str
    # ISO 3166-1 alpha-2 code for recognising phone numbers in free text,
    # otherwise derived from the spider name (e.g. "_us").
    country: str | None = None
    # LibCal only publishes hours for specific dates, not a regular weekly
    # schedule. Several weeks are requested so that holiday closures can be
    # outvoted (see `parse_opening_hours`).
    weeks: int = 4

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"https://{self.libcal_host}/api_hours_grid.php?iid={self.libcal_iid}&format=json&weeks={self.weeks}"
        )

    @cached_property
    def phone_region(self) -> str | None:
        return self.country or CountryUtils().country_code_from_spider_name(self.name)

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature | Request]:
        for location in response.json()["locations"]:
            if location.get("category") != "library" or location.get("parent_lid"):
                continue
            item = self.parse_location(location)
            yield from self.parse_item(item, location) or []

    def parse_location(self, location: dict) -> Feature:
        item = Feature()
        item["ref"] = location["lid"]
        item["branch"] = (location.get("name") or "").strip() or None
        item["website"] = (location.get("url") or "").strip() or None
        if location.get("lat") and location.get("long"):
            item["lat"] = location["lat"]
            item["lon"] = location["long"]
        self.parse_contact(item, location.get("contact") or "", self.phone_region)
        item["opening_hours"] = self.parse_opening_hours(location.get("weeks") or [])
        apply_category(Categories.LIBRARY, item)
        return item

    @staticmethod
    def parse_contact(item: Feature, contact: str, region: str | None) -> None:
        """
        Extract phone, fax, SMS and email from the free HTML `contact` field.
        `region` is the ISO 3166-1 alpha-2 code used to recognise national
        format numbers in the text; with None only "+" prefixed international
        numbers are recognised.
        """
        if not contact.strip():
            return
        sel = Selector(text=contact)
        numbers = {"phone": [], "fax": [], "sms": []}

        # Numbers in the text, classified by the label before them (e.g.
        # "Phone: ... Fax: ...") or else a label straight after them (e.g.
        # "215-751-8762 Fax", "704-216-3827 (Fax)").
        text = Selector(text=BLOCK_TAG_REGEX.sub("\n", contact)).xpath("string(.)").get() or ""
        for line in text.replace("\xa0", " ").splitlines():
            segments = [(label_type(segment), segment) for segment in LABEL_SPLIT_REGEX.split(line)]
            for i, (kind, segment) in enumerate(segments):
                matches = [m.raw_string for m in phonenumbers.PhoneNumberMatcher(segment, region)]
                if not matches:
                    continue
                if kind is None and i + 1 < len(segments):
                    next_kind, next_segment = segments[i + 1]
                    if not any(phonenumbers.PhoneNumberMatcher(next_segment, region)):
                        kind = next_kind
                numbers[kind or "phone"].extend(matches)

        if not numbers["phone"]:
            # e.g. <a href="tel:%28714%29526-7728or%28562%29694-0078">
            for href in sel.xpath('//a[starts-with(normalize-space(@href), "tel:")]/@href').getall():
                numbers["phone"].extend(filter(None, PHONE_OR_REGEX.split(unquote(href.strip()))))
            # e.g. <div class="contact-telephone" data-tel="703-228-5715" data-title="Branch Telephone Number">
            for node in sel.xpath("//*[@data-tel]"):
                if number := (node.xpath("@data-tel").get() or "").strip():
                    numbers[label_type(node.xpath("@data-title").get() or "") or "phone"].append(number)

        if numbers["phone"]:
            item["phone"] = "; ".join(numbers["phone"])
        if numbers["fax"]:
            item["extras"][Extras.FAX.value] = "; ".join(numbers["fax"])
        if numbers["sms"]:
            item["extras"]["contact:sms"] = "; ".join(numbers["sms"])

        for href in sel.xpath('//a[starts-with(normalize-space(@href), "mailto:")]/@href').getall():
            email = unquote(href.strip().removeprefix("mailto:")).split("?", 1)[0].strip()
            if EMAIL_REGEX.fullmatch(email):
                item["email"] = email
                break
        else:
            if email_match := EMAIL_REGEX.search(text):
                item["email"] = email_match.group(0)

    @staticmethod
    def normalise_time(value: str) -> str | None:
        """Convert a LibCal time such as "9am", "12:30pm" or "noon" to "9:00am" etc. for "%I:%M%p"."""
        value = OpeningHours.replace_named_times(
            value.strip().lower().replace(" ", "").replace(".", ""), NAMED_TIMES, time_24h=False
        ).lower()
        value = re.sub(r"^(\d{1,2})([ap]m)$", r"\1:00\2", value)
        return value if re.fullmatch(r"\d{1,2}:\d{2}[ap]m", value) else None

    @classmethod
    def parse_day(cls, times: dict) -> tuple | None:
        """
        Return a hashable summary of one day's hours: ("closed",), ("24hours",)
        or ("open", ((open, close), ...)); or None if unknown.

        LibCal status values:
        - "open": with a list of "hours" ranges.
        - "closed": explicitly closed.
        - "24hours": open all day.
        - "not-set": no hours entered (commonly for dates further ahead).
        - "text": free text such as "By Appointment", "Swipe 24/7",
          "Virtual Hours Only" or a link to another page; not parsed.
        - "ByApp": by appointment only; not treated as opening hours.
        Unknown statuses are also ignored.
        """
        status = times.get("status")
        if status == "closed":
            return ("closed",)
        if status == "24hours":
            return ("24hours",)
        if status == "open":
            ranges = []
            for hours in times.get("hours") or []:
                open_time = cls.normalise_time(hours.get("from") or "")
                close_time = cls.normalise_time(hours.get("to") or "")
                if not open_time or not close_time:
                    # e.g. {"from": "2pm", "to": ""} for an early closure.
                    return None
                ranges.append((open_time, close_time))
            if ranges:
                return ("open", tuple(sorted(ranges)))
        return None

    @classmethod
    def parse_opening_hours(cls, weeks: list[dict]) -> OpeningHours | str | None:
        # The API gives hours for specific dates, including one-off changes
        # such as holiday closures or early closing. To derive a regular
        # weekly schedule, several weeks are fetched and, for each weekday,
        # the most common known value is taken, so a one-off change is
        # outvoted. Days without known hours ("not-set", which is typical of
        # weeks further ahead, "text", "ByApp") are not counted. A day with
        # tied votes is left unknown, e.g. a location closed every other
        # Friday, or a closure lasting half of the weeks fetched.
        votes = {day: Counter() for day in DAYS_FULL}
        for week in weeks:
            for day in DAYS_FULL:
                if (times := (week.get(day) or {}).get("times")) and (value := cls.parse_day(times)):
                    votes[day][value] += 1
        schedule = {}
        for day, counter in votes.items():
            top = counter.most_common(2)
            if top and (len(top) == 1 or top[0][1] > top[1][1]):
                schedule[day] = top[0][0]
        if len(schedule) == 7 and all(value == ("closed",) for value in schedule.values()):
            # Closed every day, e.g. for renovation. ATP expresses such a
            # temporary closure as "Mo-Su closed".
            return "Mo-Su closed"
        if not any(value[0] != "closed" for value in schedule.values()):
            # No open day is known, e.g. only some days are closed and the
            # rest are "By appointment" or not set.
            return None
        if len(schedule) == 7 and all(value == ("24hours",) for value in schedule.values()):
            return "24/7"

        oh = OpeningHours()
        for day, value in schedule.items():
            if value[0] == "closed":
                oh.set_closed(day)
            elif value[0] == "24hours":
                oh.add_range(day, "00:00", "24:00")
            else:
                for open_time, close_time in value[1]:
                    oh.add_range(day, open_time, close_time, time_format="%I:%M%p")
        return oh

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature | Request]:
        yield item
