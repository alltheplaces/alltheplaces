import re
import time
from typing import Any, Iterable
from urllib.parse import urlsplit

from scrapy import Selector, Spider
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import Response
from scrapy.utils.sitemap import Sitemap

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

SITE = "https://bareburger.com"
DIRECTORY = f"{SITE}/locations/"
SITEMAP = f"{SITE}/page-sitemap.xml"
# A restaurant's own page, as both the locations page and the sitemap give it.
LOCATION = re.compile(r"^/locations/[^/]+/$")
# The site answers a run of requests with a holding page while it satisfies
# itself that the caller is a person. It carries a status of 200 and clears on
# a plain repeat, so such a response is simply asked for again.
VERIFYING = "request is being verified"
# "313 West 57th Street, New York, NY 10019", where the state is spelled out as
# often as it is written as a code.
ADDRESS = re.compile(r"^(?P<lead>.+?)\s*,\s*(?P<state>[A-Za-z.]+(?:\s[A-Za-z.]+)*?)\s+(?P<postcode>\d{5})(?:-\d{4})?$")
# A street with its town run on behind it and no comma between the two, as
# "33-21 31st Avenue Astoria".
RUN_ON = re.compile(
    r"^(?P<street>\d.*\b(?:Avenue|Ave|Boulevard|Blvd|Broadway|Circle|Court|Ct|Drive|Dr|Lane|Ln"
    r"|Parkway|Pkwy|Place|Pl|Plaza|Promenade|Road|Rd|Square|Street|St|Terrace|Way)\.?)\s+(?P<city>[A-Z].*)$"
)
PHONE = re.compile(r"\(?\d{3}\)?[ .-]?\d{3}[ .-]\d{4}")
# "Sun-Thur: 11:30am - 10:00pm", "Sunday - Thursday 11:00am to 9:00pm" and
# "Open Everyday 11:00am to 10:00pm" are each written on one line, one rule
# following another.
RULE = re.compile(
    r"(?P<days>[A-Za-z]+(?:\s*-\s*[A-Za-z]+)?)\s*:?\s*"
    r"(?P<opens>\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)\s*(?:-|to)\s*"
    r"(?P<closes>\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)",
    re.IGNORECASE,
)
EVERY_DAY = re.compile(r"every\s*day|daily|all\s*week", re.IGNORECASE)
ALL_WEEK = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
# A restaurant keeps neither a quarter of an hour nor a watchman's day, so a
# day stated shorter or longer than these was mis-stated rather than kept.
SHORTEST = 60
LONGEST = 18 * 60
MIDNIGHT = 24 * 60


class BareburgerUSSpider(Spider):
    """Each restaurant has a page of its own stating its address, its telephone
    number and the hours it keeps.

    Those pages are reached two ways, because neither way reaches all of them:
    the sitemap misses three of the restaurants the locations page lists, and
    the locations page misses six that the sitemap lists. Both are read and
    what they find is drawn together. One restaurant has a page under each of
    two names, and the name the two pages share tells them apart.

    The locations page is read for its addresses as well, since one restaurant
    states no address on its own page and another states no postcode there.
    Where a restaurant's own page gives a whole address, that is preferred: the
    locations page has a postcode a digit short.
    """

    name = "bareburger_us"
    # Neither the chain nor any of its restaurants has a Wikidata item.
    item_attributes = {"brand": "Bareburger"}
    allowed_domains = ["bareburger.com"]
    start_urls = [DIRECTORY]
    # About one request in twelve is held back whichever pace it is made at,
    # so the pages are asked for at a walking pace and a page held back is
    # asked for again until it comes.
    custom_settings = {"DOWNLOAD_DELAY": 0.5, "RETRY_TIMES": 6}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listed: dict[str, str] = {}
        self.seen: set[str] = set()

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        """Read the locations page, then follow every restaurant it lists.

        The card it gives each restaurant states an address, which is kept
        against that restaurant's page for the few whose own page wants one.
        Every request made from here is made after the whole page is read, so
        the addresses are all to hand by the time any of them is answered.
        """
        if retry := self.retry(response):
            yield retry
            return

        pages = []
        for link in response.css("a.elementor-button"):
            href = link.css("::attr(href)").get() or ""
            if "/locations/" not in href:
                continue
            page = self.canonical(href)
            if address := self.first_address(link.xpath('ancestor::div[contains(@class, "e-con-inner")][1]')):
                self.listed[page] = address
            pages.append(page)

        # The sitemap is read as well, for the restaurants this page omits.
        yield response.follow(SITEMAP, callback=self.parse_sitemap)
        for page in pages:
            yield response.follow(page, callback=self.parse_restaurant)

    def parse_sitemap(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for entry in Sitemap(response.body):
            if LOCATION.match(urlsplit(entry["loc"]).path):
                yield response.follow(self.canonical(entry["loc"]), callback=self.parse_restaurant)

    def parse_restaurant(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if retry := self.retry(response):
            yield retry
            return

        branch = (response.css("title::text").get() or "").strip().removesuffix("- Bareburger").strip()
        # One restaurant is published under two names of its own, and both of
        # its pages give it the same name, address and telephone number.
        if (ref := self.slug(branch)) in self.seen:
            self.logger.info(f"{response.url} states {branch} again, which is published already")
            return
        self.seen.add(ref)

        item = Feature()
        item["ref"] = ref
        item["branch"] = branch
        item["website"] = response.url

        stated = self.first_address(response) or ""
        if phone := PHONE.search(stated):
            item["phone"] = phone.group()
        written = PHONE.sub("", stated).strip(" ,")
        # Where the restaurant's own page states no whole address, the one the
        # locations page gives for it stands in.
        if not ADDRESS.match(written):
            written = self.listed.get(self.canonical(response.url)) or written
        self.parse_address(item, written, branch)

        item["opening_hours"] = self.parse_hours(response, branch)

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "burger"
        yield item

    def retry(self, response: Response) -> Any:
        if VERIFYING not in response.text:
            return None
        # Only the tally of attempts is carried over, the rest of the response's
        # own working being no business of a fresh request.
        attempted = response.request.replace(meta={"retry_times": response.meta.get("retry_times", 0)})
        return get_retry_request(attempted, spider=self, reason="awaiting verification")

    @staticmethod
    def canonical(href: str) -> str:
        """Return the one address by which a page is fetched.

        The locations page links some restaurants by path alone, some through
        the site's bare name and some through its www name, and the sitemap
        spells them a fourth way again. Written one way each is fetched once.
        """
        return f"{SITE}{urlsplit(href).path.rstrip('/')}/"

    @staticmethod
    def first_address(within: Selector | Response) -> str | None:
        """Return the first line within that reads as a street address."""
        for block in within.css(".elementor-widget-text-editor .elementor-widget-container"):
            written = re.sub(r"\s+", " ", " ".join(block.css("::text").getall())).strip()
            if written and written[0].isdigit() and len(written) < 160:
                return written
        return None

    def parse_address(self, item: Feature, written: str, branch: str) -> None:
        if not (stated := ADDRESS.match(written or "")):
            self.logger.warning(f"Unparsed address {written!r} for {branch}")
            return

        lead = stated["lead"]
        if "," in lead:
            street, city = lead.rsplit(",", 1)
        elif run_on := RUN_ON.match(lead):
            street, city = run_on["street"], run_on["city"]
        else:
            self.logger.warning(f"No town found in {lead!r} for {branch}")
            street, city = lead, None

        item["street_address"] = street.strip()
        item["city"] = city.strip() if city else None
        item["state"] = stated["state"].strip()
        item["postcode"] = stated["postcode"]
        item["country"] = "US"

    def parse_hours(self, response: Response, branch: str) -> OpeningHours | None:
        """Read the hours stated beneath the heading naming the restaurant.

        Each page states two sets of hours: those the restaurant keeps and the
        narrower ones within which it takes orders to collect and to deliver.
        Only the first are the restaurant's own.
        """
        headings = response.css("h2")
        written = None
        for position, heading in enumerate(headings):
            named = re.sub(r"\s+", " ", " ".join(heading.css("::text").getall())).strip()
            if re.search(r"\brestaurant\b", named, re.IGNORECASE) and position + 1 < len(headings):
                written = " ".join(headings[position + 1].css("::text").getall())
                break
        if not written:
            self.logger.info(f"{branch} states no hours")
            return None

        written = re.sub(r"\s+", " ", written.replace("–", "-").replace("—", "-")).strip()
        # A day stated a second time is stated to correct the first: one
        # restaurant opens all week at eleven, "except Wednesday" at noon.
        keeping: dict[str, tuple[str, str]] = {}
        for stated in RULE.finditer(written):
            if not (days := self.parse_days(stated["days"])):
                continue
            opens, closes = (self.clock(stated[part]) for part in ("opens", "closes"))
            if not self.plausible(opens, closes):
                self.logger.warning(f"Implausible hours {stated.group().strip()!r} for {branch}, so left out")
                continue
            for day in days:
                keeping[day] = (opens, closes)

        oh = OpeningHours()
        for day, (opens, closes) in keeping.items():
            oh.add_range(day, opens, closes, time_format="%I:%M%p")
        return oh if oh.as_opening_hours() else None

    @staticmethod
    def parse_days(stated: str) -> list[str]:
        if EVERY_DAY.fullmatch(stated := stated.strip()):
            return list(ALL_WEEK)
        # One page misspells a day, so a name that is not known is tried again
        # by its first three letters.
        days = [sanitise_day(part) or sanitise_day(part.strip()[:3]) for part in stated.split("-")]
        if not all(days):
            return []
        return day_range(days[0], days[-1]) if len(days) > 1 else [days[0]]

    @staticmethod
    def clock(value: str) -> str:
        value = re.sub(r"[.\s]", "", value).upper()
        hour, meridiem = value[:-2], value[-2:]
        return f"{hour if ':' in hour else hour + ':00'}{meridiem}"

    @staticmethod
    def plausible(opens: str, closes: str) -> bool:
        """Say whether a rule reads as a day of trading."""

        def minutes(value: str) -> int:
            at = time.strptime(value, "%I:%M%p")
            return at.tm_hour * 60 + at.tm_min

        opening, closing = minutes(opens), minutes(closes)
        # A restaurant closing at midnight closes at the end of its own day.
        return SHORTEST <= (closing or MIDNIGHT) - opening <= LONGEST

    @staticmethod
    def slug(value: str | None) -> str:
        return re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
