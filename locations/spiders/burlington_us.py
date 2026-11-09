import re
from typing import Any, Iterable

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc

SITE = "https://www.burlington.com"
# The pages of the chain's own store directory. Its first page states only the
# stores nearest whoever is asking, so the directory proper begins at the
# second.
PAGE = f"{SITE}/stores/page/{{}}"
FIRST = 2
# Pages are asked for in a block of this many at a time: each page that states
# a store asks for the page a block further on, so the directory is read a
# block at a time and the asking stops of itself once the pages run out.
BLOCK = 10
# A store's own page, which the directory links beside the store it states.
STORE_PAGE = re.compile(r"/stores/[a-z]{2}/[^/\"']+/(\d+)")
# The count of stores the directory gives for itself on every one of its pages.
COUNT = re.compile(r"totalCount\\?\"?:\s*(\d+)")
# How many stores a page of the directory states.
PER_PAGE = 18
# The site writes a value it has nothing for as this.
NOTHING = "$undefined"
ACTIVE = "Active"
CLOSED = "CLOSED"


class BurlingtonUSSpider(Spider):
    """The chain's own directory of stores, which states eighteen to a page.

    The search API this spider asked before is not asked any more. Asked for a
    state it answers eighteen stores however many that state holds, and gives
    the count as eighteen as well, so nothing in the answer shows that any have
    been left out: every state with more than eighteen stores was cut short,
    and 605 stores were collected of the 1,325 the directory counts. Asked for
    a postcode or a position it answers nine, which is narrower still, and it
    takes no parameter that widens either answer.

    The directory's pages overlap, each stating eighteen stores and moving on
    by nine, so every store is stated twice over and published once.

    Each page also links the page of every store it states, and those links are
    matched to the stores by the number they end with rather than by the order
    they are written in.
    """

    name = "burlington_us"
    item_attributes = {"brand": "Burlington", "brand_wikidata": "Q4999220"}
    allowed_domains = ["www.burlington.com"]
    start_urls = [PAGE.format(page) for page in range(FIRST, FIRST + BLOCK)]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen: set[str] = set()
        self.counted: int | None = None

    def closed(self, reason: str) -> None:
        """Say so if the directory counts far more stores than were read.

        The directory gives its own count of stores on every page, which is a
        check on having read all of its pages: reading only the first of them
        is how this spider came to publish 605 stores of the 1,325 counted.

        The count runs a little ahead of what the directory lists - 1,325
        against 1,316 at the time of writing - so a shortfall smaller than a
        page is the site's own and passes without remark.
        """
        if reason != "finished" or not self.counted:
            return
        if self.counted - len(self.seen) > PER_PAGE:
            self.logger.warning(f"The directory counts {self.counted} stores and only {len(self.seen)} were read")

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        pages = {number: path for path, number in self.store_pages(response)}

        stated = self.extract_stores(response)
        if self.counted is None:
            self.counted = self.extract_count(response)
        for store in stated:
            if store.get("projectStatus") != ACTIVE:
                self.logger.info(
                    f"Store {store.get('storeNumber')} is {store.get('projectStatus')}, so it is not published"
                )
                continue
            if (ref := store.get("storeNumber")) in self.seen:
                continue
            self.seen.add(ref)
            yield self.parse_store(store, pages.get(ref), response)

        if stated:
            page = int(response.url.rsplit("/", 1)[-1])
            yield response.follow(PAGE.format(page + BLOCK), callback=self.parse)

    def parse_store(self, store: dict, page: str | None, response: Response) -> Feature:
        item = DictParser.parse(store)
        # The directory states only stores in the United States.
        item["country"] = "US"
        if page:
            item["website"] = response.urljoin(page)
        if (opened := store.get("grandOpeningDate")) and opened != NOTHING:
            item["extras"]["start_date"] = opened

        item["opening_hours"] = self.parse_hours(store)

        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        return item

    def parse_hours(self, store: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            opens, closes = store.get(f"{day}Open"), store.get(f"{day}Close")
            if opens == CLOSED:
                oh.set_closed(day)
                continue
            if not opens or not closes or NOTHING in (opens, closes):
                continue
            try:
                oh.add_range(day, opens, closes, "%I:%M%p")
            except ValueError:
                self.logger.warning(
                    f"Unparsed hours {opens!r} to {closes!r} on {day} at store {store.get('storeNumber')}"
                )
        return oh

    @staticmethod
    def store_pages(response: Response) -> Iterable[tuple[str, str]]:
        for found in STORE_PAGE.finditer(response.text):
            yield found.group(), found.group(1)

    @staticmethod
    def extract_count(response: Response) -> int | None:
        """Return the count of stores the directory gives for itself."""
        if found := COUNT.search(response.text):
            return int(found.group(1))
        return None

    def extract_stores(self, response: Response) -> list[dict]:
        """Walk the stores out of the data the page was built from."""
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for _, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        stores: dict[str, dict] = {}
        self.find_stores(dict(parse_rsc(rsc.encode())), stores)
        return list(stores.values())

    def find_stores(self, node: Any, stores: dict) -> None:
        if isinstance(node, dict):
            if "storeNumber" in node and "projectStatus" in node:
                stores[node["storeNumber"]] = node
            for value in node.values():
                self.find_stores(value, stores)
        elif isinstance(node, list):
            for value in node:
                self.find_stores(value, stores)
