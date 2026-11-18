import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser

# A street is stated behind the store's own label, which usually carries its number:
# "YCC - AURORA OH #0351, 549 SOUTH CHILLCOTHE ROAD". At the outlet malls the label
# names the mall and carries no number, and is cut short: "YCC - Grand Prairie
# Premium Ou, 2950 West Interstate 20".
STORE_CODE = re.compile(r"^\s*YCC\s*-\s*[^,]*?(?:#\s*(?P<number>\d+))?\s*,\s*(?P<street>.+)$", re.IGNORECASE)
CANADA = {"AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"}


class YankeeCandleSpider(Spider):
    """Each store states itself as linked data, and the locator reaches them a state at
    a time.

    A state's page lists the chain's own stores first and then two sets of other
    people's shops, under "Authorized Dealers" and "WoodWick Retailers". Only the
    chain's own stores are followed, by taking the links from that section alone.
    """

    name = "yankee_candle"
    item_attributes = {"brand": "Yankee Candle", "brand_wikidata": "Q8048733"}
    start_urls = ["https://www.yankeecandle.com/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for url in response.xpath('//a[contains(@href, "/stores/")]/@href').getall():
            yield response.follow(url, callback=self.parse_state)

    def parse_state(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for heading in response.xpath('//h3[contains(., "Stores in")]'):
            for sibling in heading.xpath("following-sibling::*"):
                # The next heading starts the dealers, who are not this chain.
                if sibling.root.tag == "h3":
                    break
                for url in sibling.xpath('.//a[contains(@href, "/stores/")]/@href').getall():
                    yield response.follow(url, callback=self.parse_store)

    def parse_store(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if not (store := self.linked_data(response)):
            self.logger.warning(f"No store data on {response.url}")
            return

        # Two stores are stated as opening at midnight on a Sunday and closing at six,
        # where every other day of their week opens at ten. That is a slip in the
        # source rather than a night shift, so the day is left without hours.
        specification = store.get("openingHoursSpecification")
        if isinstance(specification, list):
            kept = []
            for day in specification:
                if isinstance(day, dict) and day.get("opens") == "00:00" and day.get("closes") not in ("24:00", None):
                    self.logger.warning(
                        f"{response.url} opens at midnight on {day.get('dayOfWeek')}, so that day is skipped"
                    )
                    continue
                kept.append(day)
            store = {**store, "openingHoursSpecification": kept}

        item = LinkedDataParser.parse_ld(store)
        # The name is a line of search engine filler that repeats the address and the
        # store number, so the town is what each store is known by instead.
        item.pop("name", None)
        item["branch"] = self.titlecase(item.get("city"))
        item["city"] = self.titlecase(item.get("city"))

        # The street is published behind the store's internal code, which is also the
        # only number the site states for a store, so it is kept as the reference.
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        if parts := STORE_CODE.match(item.get("street_address") or ""):
            item["street_address"] = self.titlecase(parts["street"])
            if parts["number"]:
                item["extras"]["ref:yankee_candle"] = parts["number"]
        else:
            item["street_address"] = self.titlecase(item.get("street_address"))

        # Every store states its country as the word "null".
        item["country"] = self.country(item.get("state"))
        # The site writes its own address with a doubled slash in it.
        item["website"] = re.sub(r"(?<!:)//+", "/", response.url)

        apply_category(Categories.SHOP_CANDLES, item)
        yield item

    def linked_data(self, response: Response) -> dict:
        for blob in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(blob)
            except json.JSONDecodeError:
                self.logger.warning(f"Unparsed linked data on {response.url}")
                continue
            if found := self.walk(data):
                return found
        return {}

    @staticmethod
    def walk(node: Any) -> dict:
        if isinstance(node, dict):
            if node.get("@type") == "LocalBusiness":
                return node
            for value in node.values():
                if found := YankeeCandleSpider.walk(value):
                    return found
        elif isinstance(node, list):
            for value in node:
                if found := YankeeCandleSpider.walk(value):
                    return found
        return {}

    def country(self, state: str | None) -> str:
        if (state or "").upper() in CANADA:
            return "CA"
        if (state or "").upper() == "PR":
            return "PR"
        return "US"

    @staticmethod
    def titlecase(value: str | None) -> str | None:
        """Take the shouting out of an address, which is published in capitals.

        A word carrying a digit, such as a route number, is left as it is.
        """
        if not value:
            return None
        words = []
        for word in value.split():
            if any(char.isdigit() for char in word):
                words.append(word)
            else:
                # Each run of letters is capitalised on its own, so that a name like
                # O'FALLON does not come out as O'fallon.
                words.append(re.sub(r"[^\W\d_]+", lambda run: run.group().capitalize(), word))
        return " ".join(words) or None
