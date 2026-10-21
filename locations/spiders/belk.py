import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response
from twisted.python.failure import Failure

from locations.categories import Categories, apply_category
from locations.items import Feature

DIRECTORY = "https://www.belk.com/customer-service/store-directory/"
# "Alabaster, AL 35007-3112"
LOCALITY = re.compile(r"^(?P<city>.+),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5}(?:-\d{4})?)$")


class BelkSpider(Spider):
    """The store directory states every store's address and phone number, and is the
    only part of the site that can be read.

    Each row also links a store page, which is the one place coordinates are
    published, but those pages cannot be fetched: they answer 403 to an ordinary
    request and the proxy is given a website ban for them, so asking for all 291 of
    them spends a request each to learn nothing. They are not requested, and no
    coordinates are published.

    Reading the rows rather than the pages also takes in the stores whose page could
    never be read anyway. The pages are keyed on the StoreID in the query string
    rather than on the slug in the path, and the StoreIDs are not dependable: 14
    Mississippi stores are all listed as StoreID=000, 14 more carry an ID whose page
    is an unresolved server-side include to a path robots.txt disallows, and Jackson
    TN is listed under the ID that belongs to Cape Coral FL, whose page it is served.

    The directory itself is refused as well, often enough that a plain fetch of it
    returned all 291 stores earlier in a day and nothing but bans later the same day.
    It is the only page asked for and there is no second source for it, so it is
    rendered in a browser and asked for again when a refusal comes back.
    """

    name = "belk"
    item_attributes = {"brand": "Belk", "brand_wikidata": "Q127428"}
    allowed_domains = ["www.belk.com"]
    requires_proxy = True
    custom_settings = {
        # A plain fetch of this site through the proxy is answered with a website ban,
        # so the page is rendered in a browser instead. It has to be set here rather
        # than on the request: the proxy middleware overwrites zyte_api_automap on
        # every request, and naming the parameters on the request itself is refused
        # for mixing manual and mapped parameters.
        "ZYTE_API_AUTOMAP_PARAMS": {"browserHtml": True},
        # No user agent of our own is set: the proxy warns on every request that one
        # weakens its ban avoidance, and a ban is what this site answers with.
        # Spaces the attempts out, so they are not all made inside one refusal.
        "DOWNLOAD_DELAY": 3,
    }
    # A render costs the proxy around twenty seconds and it retries each one itself,
    # so this is as many attempts as fit in the time a run is given.
    max_attempts = 3

    async def start(self) -> AsyncIterator[Request]:
        # The first attempt needs the errback too: a refused request is how the run
        # ends up with nothing, and that is the attempt most often refused.
        yield Request(DIRECTORY, callback=self.parse, cb_kwargs={"attempt": 1}, errback=self.on_error)

    def parse(self, response: Response, attempt: int = 1, **kwargs: Any) -> Iterable[Any]:
        rows = response.xpath('//table[contains(@class, "data-table")]//tr[.//a[contains(@href, "StoreID=")]]')
        if not rows:
            # A refusal still answers 200, with a page that has no store table on it.
            yield from self.again(attempt, f"no store rows in {len(response.text)} bytes")
            return

        for row in rows:
            cells = [text for cell in row.xpath("./td//text()").getall() if (text := re.sub(r"\s+", " ", cell).strip())]
            if len(cells) != 4:
                self.logger.warning(f"Unexpected store row: {cells!r}")
                continue
            name, street, locality, phone = cells

            item = Feature()
            # Neither identifier the directory publishes can be used: the StoreID is
            # shared or a placeholder, and one store is linked with another's slug.
            # The names are the only values that are unique to a store.
            item["ref"] = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.casefold())).strip("-")
            item["branch"] = re.sub(r"^Belk\s+", "", name)
            item["street_address"] = street
            item["phone"] = phone
            # The chain trades in 16 states and nowhere else. Without this the country
            # has nothing to be read from, and the phone numbers, which the directory
            # states without a dialling code, cannot be normalised.
            item["country"] = "US"
            if parts := LOCALITY.match(locality):
                item["city"] = parts["city"]
                item["state"] = parts["state"]
                item["postcode"] = parts["postcode"]
            else:
                self.logger.warning(f"Unparsed locality: {locality!r}")

            item["website"] = response.urljoin(row.xpath('.//a[contains(@href, "StoreID=")]/@href').get())
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            yield item

    def on_error(self, failure: Failure) -> Iterable[Request]:
        """Ask again when the request itself failed, which is how a ban arrives."""
        # The reason a proxy error gives is at the end of it, past a long repeat of the
        # request, so the end is what gets logged.
        error = repr(failure.value)
        yield from self.again(
            failure.request.cb_kwargs.get("attempt", 1),
            f"{type(failure.value).__name__} ending {error[-400:]}" if len(error) > 400 else error,
        )

    def again(self, attempt: int, reason: str) -> Iterable[Request]:
        if attempt >= self.max_attempts:
            self.logger.error(f"No store directory after {attempt} attempts, most recently: {reason}")
            return
        self.logger.warning(f"Asking for the store directory again, attempt {attempt + 1}: {reason}")
        yield Request(
            DIRECTORY,
            callback=self.parse,
            cb_kwargs={"attempt": attempt + 1},
            errback=self.on_error,
            dont_filter=True,
        )
