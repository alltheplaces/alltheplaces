import json
from datetime import date
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


def to_date(value: dict | str) -> date | None:
    return date(value["year"], value["month"], value["day"]) if value else None


class MangeonsFraisFRSpider(SitemapSpider):
    name = "mangeons_frais_fr"
    item_attributes = {"brand_wikidata": "Q130215824"}
    sitemap_urls = ["https://magasins.mangeonsfrais.com/sitemap_pois.xml"]
    sitemap_rules = [(r"/details$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        next_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        poi = next_data["props"]["pageProps"]["poiData"]["poi"]
        metadata = poi["metadata"]
        status = metadata["status"]
        opened, closed = to_date(status["OpenedFrom"]), to_date(status["ClosedFrom"])
        if not status["Published"] or (opened and opened > date.today()) or (closed and closed <= date.today()):
            return

        item = Feature()
        item["ref"] = poi["code"]
        item["website"] = response.url
        item["branch"] = metadata["details"]["Name"].removeprefix("Mangeons Frais").strip().title()
        item["lat"] = poi["position"]["Latitude"]
        item["lon"] = poi["position"]["Longitude"]
        item["street_address"] = poi["address"]["AddressLine1"]
        item["city"] = poi["address"]["City"]
        item["postcode"] = poi["address"]["PostalCode"]
        item["phone"] = metadata["contacts"]["Phone"]

        item["opening_hours"] = OpeningHours()
        for day in poi["schedules"]["Defaultweekschedule"]:
            if not day["values"]["IsOpen"]:
                item["opening_hours"].set_closed(day["name"])
            for rng in day["values"]["OpeningRanges"]:
                begin, end = rng["BeginTime"], rng["EndTime"]
                item["opening_hours"].add_range(
                    day["name"],
                    f'{begin["Hour"]:02d}:{begin["Minute"]:02d}',
                    f'{end["Hour"]:02d}:{end["Minute"]:02d}',
                )
        yield item
