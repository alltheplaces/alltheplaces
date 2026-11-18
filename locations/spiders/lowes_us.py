import json
import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response
from twisted.python.failure import Failure

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import FIREFOX_LATEST

STORE_SITEMAP = "https://www.lowes.com/sitemap/store0.xml"
DIRECTORY_SITEMAP = "https://www.lowes.com/sitemap/storedirectory0.xml"
PRELOADED = re.compile(r"window\.__PRELOADED_STATE__\s*=\s*(\{)", re.IGNORECASE)
LOCATIONS = re.compile(r"<loc>(?:<!\[CDATA\[)?([^<\]]+)")


class LowesUSSpider(Spider):
    """A store's own page is refused with a 403, so the stores are read from the state
    directories instead, where the page states them all in its preloaded state.

    Those directories state no coordinates and no opening hours: the only page that
    did was the store's own. The store sitemap is still read, because it names each
    store's page by the same id the directory gives, which is where `website` comes
    from.
    """

    name = "lowes_us"
    # The brand is set per store rather than for the spider, because 16 of them trade
    # as Lowe's Outlet, which has no Wikidata item of its own to carry.
    allowed_domains = ["lowes.com"]
    custom_settings = {"USER_AGENT": FIREFOX_LATEST}
    requires_proxy = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.websites: dict[str, str] = {}

    async def start(self) -> AsyncIterator[Request]:
        # Asked for with an errback, so that a run still reaches the directories when
        # the store sitemap cannot be had; it only supplies each store's own address.
        yield Request(STORE_SITEMAP, callback=self.parse, errback=self.no_store_sitemap)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        # "https://www.lowes.com/store/OH-Columbus/0181" is store 0181.
        for url in LOCATIONS.findall(response.text):
            if store := re.search(r"/(\d{4})/?$", url):
                self.websites[store.group(1)] = url
        yield from self.directories()

    def no_store_sitemap(self, failure: Failure) -> Iterable[Request]:
        """Carry on without the store pages' addresses, which only name them."""
        self.logger.warning(f"No store sitemap, so no website for any store: {failure.value}")
        yield from self.directories()

    def directories(self) -> Iterable[Request]:
        yield Request(DIRECTORY_SITEMAP, callback=self.parse_directory)

    def parse_directory(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for url in LOCATIONS.findall(response.text):
            # A state's directory is "/Lowes-Stores/Ohio/OH"; the two pages that index
            # the states themselves are not.
            if re.search(r"/Lowes-Stores/[^/]+/[A-Z]{2}$", url):
                yield response.follow(url, callback=self.parse_state)

    def parse_state(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if not (stores := self.preloaded(response).get("storeDirectory")):
            self.logger.warning(f"No stores in the directory at {response.url}")
            return

        # The directory is keyed by town, each holding the stores in it.
        for town in stores.values():
            for store in town or []:
                item = Feature()
                item["ref"] = store.get("id")
                self.name_and_brand(item, store.get("storeName"))
                item["street_address"] = self.titlecase(store.get("address"))
                item["city"] = store.get("city")
                item["state"] = store.get("state")
                item["postcode"] = store.get("zip")
                item["phone"] = store.get("phone")
                item["country"] = store.get("country")
                item["website"] = self.websites.get(store.get("id"))
                # Every store in a state is given the same list of features, so they
                # describe the chain rather than any one store and are not read.
                apply_category(Categories.SHOP_DOITYOURSELF, item)
                yield item

    def preloaded(self, response: Response) -> dict:
        """Return the state the page is built from, which trails the rest of the page."""
        if not (start := PRELOADED.search(response.text)):
            return {}
        try:
            return json.JSONDecoder().raw_decode(response.text[start.start(1) :])[0]
        except json.JSONDecodeError:
            self.logger.warning(f"Unparsed preloaded state on {response.url}")
            return {}

    @staticmethod
    def name_and_brand(item: Feature, name: str | None) -> None:
        """Set which Lowe's a store is, and what it is called without that in front.

        The stores are named "Cheyenne Lowe's", and the clearance stores "Lowe's
        Outlet Houston" or "Lowe's Outlet of Baltimore", one of them in capitals.
        """
        name = re.sub(r"\s+", " ", (name or "").replace("’", "'")).strip()
        if outlet := re.match(r"Lowe'?s\s+Outlet\s+(?:of\s+)?(?P<branch>.+)", name, flags=re.IGNORECASE):
            item["brand"] = "Lowe's Outlet"
            branch = outlet["branch"]
        else:
            item["brand"] = "Lowe's"
            item["brand_wikidata"] = "Q1373493"
            branch = re.sub(r"^Lowe'?s\s+of\s+|\s*Lowe'?s$", "", name, flags=re.IGNORECASE)
        # One store's name ends with its state, which the item already states.
        branch = re.sub(r",\s*[A-Z]{2}$", "", branch.strip())
        item["branch"] = LowesUSSpider.titlecase(branch) or None

    @staticmethod
    def titlecase(value: str | None) -> str | None:
        """Take the shouting out of an address, which is published in capitals."""
        if not value:
            return None
        words = []
        for word in value.split():
            if any(char.isdigit() for char in word):
                words.append(word)
            else:
                words.append(re.sub(r"[^\W\d_]+", lambda run: run.group().capitalize(), word))
        return " ".join(words) or None
