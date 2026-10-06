import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class YvesRocherSpider(Spider):
    name = "yves_rocher"
    # NSI excludes AT, CH and DE, so it doesn't backfill the name there.
    item_attributes = {"brand": "Yves Rocher", "brand_wikidata": "Q1477321", "name": "Yves Rocher"}
    # "/stores/SL" serves the store locator on every site, including those that don't link to one (AT, DE, CH).
    start_urls = [
        f"https://{domain}/stores/SL"
        for domain in [
            "www.yves-rocher.fr",
            "www.yves-rocher.es",
            "www.yves-rocher.be",
            "www.yvesrocher.ca",
            "www.yvesrocher.com.tr",
            "www.yves-rocher.ua",
            "www.yves-rocher.cz",
            "www.yves-rocher.pl",
            "www.yves-rocher.ro",
            "www.yves-rocher.at",
            "www.yves-rocher.de",
            "www.yves-rocher.ch",
        ]
    ]
    requires_proxy = True
    # Zyte gets a "Website Ban" with the default bot user agent.
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: TextResponse, **kwargs: Any) -> Any:
        # Some locales embed every store in the page, the others only link to store pages.
        links = response.css("#all-store-container a[href*='/S-']::attr(href)").getall()
        script = response.xpath('//script[contains(text(), "data = JSON.parse(")]/text()').get("")
        match = re.search(r"data = JSON.parse\((.+)\);", script)
        if match and (stores := DictParser.get_nested_key(json.loads(json.loads(match.group(1))), "allStores")):
            # The embedded "uri" lacks the language prefix (e.g. /en/) that the listed links have.
            websites = {link.rsplit("/S-", 1)[1]: response.urljoin(link) for link in links}
            for location in stores:
                yield from self.parse_location(location, websites.get(location["storeId"]))
        else:
            yield from response.follow_all(links, callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        if data := response.css("[data-woosmap-component]::attr(data-woosmap-component)").get():
            yield from self.parse_location(json.loads(data), response.url)

    def parse_location(self, location: dict, website: str | None) -> Iterable[Feature]:
        opening_rules = {day: location.get(f"opening{day}") for day in DAYS_FULL}
        # Head-office (ES "VAD") and inactive (CZ, PL) entries have neither coordinates nor hours.
        if location.get("location") in (None, [0, 0]) and not any(opening_rules.values()):
            return
        if coordinates := location.pop("location", None):
            location["lon"], location["lat"] = coordinates
        location["street_address"] = merge_address_lines(
            [location.pop("address1", None), location.pop("address2", None)]
        )
        item = DictParser.parse(location)

        # The Andorra store is listed on the Spanish site as "YR-ES".
        if (location.get("zipCode") or "").startswith("AD"):
            item["country"] = "AD"
        else:
            item["country"] = location["countryCode"].removeprefix("YR-")
        # CZ, PL and RO store ids are bare numbers that repeat across countries.
        store_id = location["storeId"]
        item["ref"] = f"{item['country']}{store_id}" if store_id.isdigit() else store_id
        item["branch"] = (
            re.sub(r"^yves rocher\s+", "", item.pop("name", None) or "", flags=re.IGNORECASE).strip() or None
        )
        if item.get("city"):
            item["city"] = re.sub(r"\s*\(.*\)\s*$", "", item["city"])
        if item.get("phone") and not re.search(r"\d", item["phone"]):
            item["phone"] = None
        # Turkish postcodes lost their leading zero (provinces 01-09).
        if item["country"] == "TR" and item.get("postcode"):
            item["postcode"] = item["postcode"].zfill(5)
        item["website"] = website

        # Status 2 stores (seen in FR) show every day as closed on their page, whatever their opening fields say.
        if location.get("status") == 2:
            set_closed(item)
        else:
            item["opening_hours"] = OpeningHours()
            for day, rule in opening_rules.items():
                if rule:
                    for start_time, end_time in re.findall(r"(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", rule):
                        item["opening_hours"].add_range(day, start_time, end_time)

        apply_category(Categories.SHOP_COSMETICS, item)

        yield item
