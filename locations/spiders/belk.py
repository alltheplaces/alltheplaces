import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

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
    """

    name = "belk"
    item_attributes = {"brand": "Belk", "brand_wikidata": "Q127428"}
    allowed_domains = ["www.belk.com"]
    # The chain only trades in the United States.
    requires_proxy = "US"

    async def start(self) -> AsyncIterator[Request]:
        # Belk's edge answers 403 to an ordinary request, and bans the proxy's plain
        # fetch of the page, so the directory is asked for through a browser. No user
        # agent is set either: Zyte warns that one of our own weakens its ban
        # avoidance, and this site is where that shows.
        yield Request(
            "https://www.belk.com/customer-service/store-directory/",
            meta={"zyte_api": {"browserHtml": True, "geolocation": "US"}},
        )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for row in response.xpath('//table[contains(@class, "data-table")]//tr[.//a[contains(@href, "StoreID=")]]'):
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
