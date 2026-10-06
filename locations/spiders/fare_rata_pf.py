import json
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature


class FareRataPfSpider(Spider):
    name = "fare_rata_pf"
    # Fare Rata is the postal company of the OPT group (Q3349602); it has no Wikidata item of its own.
    item_attributes = {"operator": "Fare Rata"}
    allowed_domains = ["www.farerata.pf"]
    # The map page embeds the office list ("markersData"); each office has a JSON detail endpoint.
    start_urls = ["https://www.farerata.pf/fr/vos-bureaux-de-poste"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        start = response.text.find("markersData = [")
        offices = json.JSONDecoder().raw_decode(response.text, start + len("markersData = "))[0]
        for office in offices:
            yield JsonRequest(
                f"https://www.farerata.pf/fr/vos-bureaux-de-poste/{office['id']}/detail", callback=self.parse_office
            )

    def parse_office(self, response: Response) -> Any:
        office = response.json()
        item = Feature()
        item["ref"] = office["id"]
        item["branch"] = office["nom"]
        item["lat"], item["lon"] = office["latitude"], office["longitude"]
        item["postcode"] = str(office.get("codePostal") or "")
        item["city"] = office.get("nom")
        item["state"] = office.get("archipel")
        item["extras"]["addr:island"] = office.get("ile")
        item["country"] = "PF"
        item["phone"] = office.get("numeroTelephone")
        if office.get("code"):
            item["extras"]["ref:fare_rata"] = str(office["code"])
        oh = OpeningHours()
        for day in office.get("jours") or []:
            day_name = DAYS_FR.get(day["jour"].title())
            for slot in day.get("horaires") or []:
                if slot.get("heureFermeture"):
                    oh.add_range(day_name, slot["heureOuverture"], slot["heureFermeture"])
                elif (slot.get("heureOuverture") or "").lower().startswith("ferm"):
                    oh.set_closed(day_name)
        item["opening_hours"] = oh
        apply_category(Categories.POST_OFFICE, item)
        yield item
