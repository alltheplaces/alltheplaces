from datetime import date
from typing import Any, Iterable, Iterator

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc


def walk(obj: Any) -> Iterator[Any]:
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


class PlayinFRSpider(Spider):
    name = "playin_fr"
    item_attributes = {"brand": "Playin", "brand_wikidata": "Q141957938"}
    allowed_domains = ["www.play-in.com"]
    start_urls = ["https://www.play-in.com/fr/magasins"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for link in set(response.xpath('//a[re:test(@href, "^/fr/magasin/\\d+/")]/@href').getall()):
            yield response.follow(link, self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for n, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        data = dict(parse_rsc(rsc.encode()))

        store = center = None
        for obj in walk(data):
            if not isinstance(obj, dict):
                continue
            if store is None and obj.get("__typename") == "Store" and "weekPlanning" in obj:
                store = obj
            if center is None and isinstance(obj.get("center"), list):
                center = obj["center"]
        if store is None:
            return

        item = Feature()
        item["ref"] = str(store["_id"])
        item["branch"] = store["shortName"]
        item["street_address"] = store["address"]
        item["city"] = store["city"]
        item["postcode"] = store["zipCode"]
        item["country"] = "FR"
        item["phone"] = store.get("phoneNumber")
        item["email"] = store.get("contactEmail")
        item["website"] = response.url
        if center:
            item["lat"], item["lon"] = center

        item["opening_hours"] = self.parse_hours(store.get("weekPlanning") or {})

        apply_category(Categories.SHOP_GAMES, item)
        yield item

    def parse_hours(self, week_planning: dict) -> OpeningHours | None:
        # weekPlanning holds the coming week by date; exceptional days are skipped
        oh = OpeningHours()
        days = set()
        for day_date, planning in week_planning.items():
            if planning.get("isExceptional"):
                continue
            day = DAYS[date.fromisoformat(day_date).weekday()]
            days.add(day)
            if not planning.get("isOpen"):
                oh.set_closed(day)
                continue
            for hours in planning.get("hours") or []:
                oh.add_range(day, hours["from"][11:16], hours["to"][11:16])
        if len(days) < 7:
            return None
        return oh
