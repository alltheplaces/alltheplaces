import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

MARKETS = "https://drafthouse.com/s/mother/v1/page/cclamp"
MARKET = "https://drafthouse.com/s/mother/v1/market/{}"


class AlamoDrafthouseUSSpider(Spider):
    """The site is a single page application served off its own API, which lists the
    cinemas by market rather than all at once, so each market is asked for in turn.

    The market endpoint is used rather than the market's schedule, which carries the
    same cinemas behind a megabyte and a half of showtimes, and rather than the
    locator's own summaries, which state an address but no coordinates.

    Not to be confused with the `alamo` spider, which is Alamo Rent A Car.
    """

    name = "alamo_drafthouse_us"
    item_attributes = {"brand": "Alamo Drafthouse Cinema", "brand_wikidata": "Q4705954"}
    start_urls = [MARKETS]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for market in response.json()["data"]["marketSummaries"]:
            yield response.follow(MARKET.format(market["id"]), callback=self.parse_market)

    def parse_market(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        market = response.json()["data"]["market"]
        for cinema in market.get("cinemas") or []:
            # Each cinema states whether it is trading, which is how one that has
            # closed or has yet to open would be told apart from the rest.
            if cinema.get("status") != "OPEN":
                self.logger.info(f"Skipping {cinema.get('slug')!r}, which is {cinema.get('status')!r}")
                continue

            item = Feature()
            item["ref"] = cinema["id"]
            # One cinema is named with the brand in front of it, and the rest are not.
            item["branch"] = re.sub(r"^Alamo\s+Drafthouse\s+", "", cinema["name"] or "").strip() or None
            item["lat"] = cinema.get("latitude")
            item["lon"] = cinema.get("longitude")
            item["street_address"] = clean_address([cinema.get("street1"), cinema.get("street2")])
            item["city"] = cinema.get("city")
            item["state"] = cinema.get("state")
            item["postcode"] = cinema.get("postalCode")
            item["phone"] = cinema.get("phone")
            item["email"] = cinema.get("email")
            item["website"] = f"https://drafthouse.com/{market['slug']}/theater/{cinema['slug']}"

            apply_category(Categories.CINEMA, item)
            yield item
