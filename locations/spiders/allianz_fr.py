import json
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# Exact postcodes take precedence: Saint-Martin and Saint-Barthélemy share the 971 prefix.
NON_FR_POSTCODE_COUNTRIES = {
    "97150": "MF",
    "97133": "BL",
    "971": "GP",
    "972": "MQ",
    "973": "GF",
    "974": "RE",
    "975": "PM",
    "976": "YT",
    "980": "MC",
    "986": "WF",
    "987": "PF",
    "988": "NC",
}


class AllianzFRSpider(SitemapSpider):
    name = "allianz_fr"
    item_attributes = {"brand": "Allianz", "brand_wikidata": "Q487292", "name": "Allianz"}
    sitemap_urls = ["https://agences.allianz.fr/sitemap_index.xml"]
    sitemap_follow = ["sitemap_geo"]
    # Department pages list all their agencies; Monaco has no department, only a city page.
    sitemap_rules = [(r"/assurances/(?:[a-z0-9-]+-(?:\d{2,3}|2[AB])|monaco-98000-C\d+)$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        next_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get(""))
        for poi in next_data["props"]["pageProps"]["dualFrameData"]["poisListData"]:
            # TSA (Tri Service Arrivée) is a company mail-sorting address, not a physical location.
            if poi["address"]["AddressLine1"].startswith("TSA"):
                continue
            contacts = poi["metadata"]["contacts"]
            item = Feature()
            item["ref"] = poi["code"]
            item["branch"] = poi["metadata"]["details"]["Name"].title()
            item["lat"] = poi["position"]["Latitude"]
            item["lon"] = poi["position"]["Longitude"]
            item["street_address"] = poi["address"]["AddressLine1"].title()
            item["city"] = poi["address"]["City"].title()
            postcode = item["postcode"] = poi["address"]["PostalCode"]
            if country := NON_FR_POSTCODE_COUNTRIES.get(postcode) or NON_FR_POSTCODE_COUNTRIES.get(postcode[:3]):
                item["country"] = country
            apply_category(Categories.OFFICE_INSURANCE, item)
            item["phone"] = contacts["Phone"]
            item["email"] = contacts["Mail"]
            item["website"] = contacts["Web"]

            schedule = poi["schedules"]["Defaultweekschedule"]
            # IsOpen is false on every day when the agency has no hours entered, which is not "closed".
            if any(day["values"]["IsOpen"] for day in schedule):
                item["opening_hours"] = OpeningHours()
                for day in schedule:
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
