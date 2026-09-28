import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ProxiFRSpider(Spider):
    name = "proxi_fr"
    item_attributes = {"brand": "Proxi", "brand_wikidata": "Q3408522"}
    start_urls = ["https://www.myproxi.fr/ajax/commerces/3000/0"]

    def parse(self, response: TextResponse, **kwargs: Any) -> Any:
        for location in response.json():
            # 7 is "Affiliation en cours" on the site; 2 is hidden by the site itself.
            if location["Statut"] in (2, 7):
                continue
            # Loyalty-balance takeover accounts ("Reprise Solde") have no address.
            if not location.get("AdresseA"):
                continue
            activities = [activity["Libelle"] for activity in (location.get("magasin") or {}).get("activites") or []]
            if any("caisses enregistreuses" in activity for activity in activities):
                continue
            path = location["s_e_o_urns"][0]["Urn"] if location["s_e_o_urns"] else f"pro/{location['IDPointDeVente']}"
            yield response.follow(f"/{path}", self.parse_store, cb_kwargs={"location": location})

    def parse_store(self, response: Response, location: dict) -> Iterable[Feature]:
        store = json.loads(response.xpath("//header-actions/@*[name()=':pdv']").get("{}"))

        item = Feature()
        item["ref"] = location["IDPointDeVente"]
        item["lat"] = location["Latitude"]
        item["lon"] = location["Longitude"]
        item["street_address"] = merge_address_lines([location["AdresseA"], location["AdresseB"], location["AdresseC"]])
        item["postcode"] = location["CodePostal"]
        item["city"] = location["Ville"]
        item["phone"] = location["Telephone"]
        # The list's first URN can be an old slug (e.g. a former Vival); og:url is the current one.
        item["website"] = response.xpath('//meta[@property="og:url"]/@content').get("").strip() or response.url

        # "Enseigne" is free text set by each store, often its legal entity name, so it's not used as name.
        names = f"{location.get('Enseigne')} {(store.get('magasin') or {}).get('Enseigne')}"
        if re.search(r"proxi\s*super", names, re.IGNORECASE):
            item["name"] = "Proxi Super"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        else:
            item["name"] = "Proxi"
            apply_category(Categories.SHOP_CONVENIENCE, item)

        schedule = store.get("Horaires")
        if isinstance(schedule, dict) and (days := schedule.get("horaire_joures")):
            oh = OpeningHours()
            for day in days:
                if not day["Ouvert"]:
                    oh.set_closed(DAYS[day["Jour"] - 1])
                    continue
                for hours in day.get("horaire_heure") or []:
                    oh.add_range(DAYS[day["Jour"] - 1], hours["De"], hours["A"])
            item["opening_hours"] = oh

        yield item
