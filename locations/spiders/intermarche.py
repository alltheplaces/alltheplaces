import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class IntermarcheSpider(scrapy.Spider):
    name = "intermarche"
    allowed_domains = ["intermarche.com"]
    INTERMARCHE = {
        "brand": "Intermarché",
        "brand_wikidata": "Q3153200",
    }
    INTERMARCHE_SUPER = {
        "brand": "Intermarché Super",
        "brand_wikidata": "Q98278038",
    }
    INTERMARCHE_CONTACT = {
        "brand": "Intermarché Contact",
        "brand_wikidata": "Q98278049",
    }
    INTERMARCHE_EXPRESS = {
        "brand": "Intermarché Express",
        "brand_wikidata": "Q98278043",
    }
    INTERMARCHE_HYPER = {
        "brand": "Intermarché Hyper",
        "brand_wikidata": "Q98278022",
    }
    item_attributes = {"country": "FR"}
    requires_proxy = True

    def start_requests(self):
        yield JsonRequest(
            url="https://www.intermarche.com/api/service/pdvs/v4/pdvs/zone?min=20000",
        )

    def parse(self, response, **kwargs):
        for place in response.json()["resultats"]:
            place["ref"] = place["entityCode"]

            if len(place.get("addresses", [])) > 0:
                place["address"] = place["addresses"][0]
                place["address"]["street_address"] = place["address"].pop("address")
                place["address"]["city"] = place["address"].pop("townLabel")
                place["longitude"] = place["address"].pop("longitude")
                place["latitude"] = place["address"].pop("latitude")

            for contact in place.get("contacts", []):
                if contact.get("contactCode") == "telephone":
                    place["phone"] = contact.get("contactValue")
                    break

            item = DictParser.parse(place)

            slug = f'{item["ref"]}/{item["city"].replace(" ", "-")}-{item["postcode"]}/infos-pratiques'
            item["website"] = f"https://www.intermarche.com/magasins/{slug}"

            oh = OpeningHours()
            for rules in place["calendar"]["openingHours"]:
                for i, d in enumerate(rules["days"]):
                    if d == "1":
                        oh.add_range(DAYS[i], rules["startHours"], rules["endHours"])
            item["opening_hours"] = oh.as_opening_hours()

            apply_yes_no(Extras.ATM, item, any(s["code"] == "dis" for s in place["ecommerce"]["services"]), False)

            if place.get("modelLabel") in [
                "SUPER ALIMENTAIRE",
                "SUPER GENERALISTE",
            ]:
                item.update(self.INTERMARCHE_SUPER)
            elif place.get("modelLabel") == "CONTACT":
                item.update(self.INTERMARCHE_CONTACT)
            elif place.get("modelLabel") == "EXPRESS":
                item.update(self.INTERMARCHE_EXPRESS)
            elif place.get("modelLabel") == "HYPER":
                item.update(self.INTERMARCHE_HYPER)
            elif place.get("modelLabel") == "Réservé Soignants":
                continue  # Drive through stores reserved for medical workers
            elif place.get("modelLabel") == "Retrait La Poste":
                continue  # Something to do with post offices

            if any(s["code"] == "ess" for s in place["ecommerce"]["services"]):
                fuel = item.copy()
                fuel["ref"] += "_fuel"
                fuel.update(self.INTERMARCHE)

                apply_category(Categories.FUEL_STATION, fuel)

                yield fuel

            if any(s["code"] == "lav" for s in place["ecommerce"]["services"]):
                car_wash = item.copy()
                car_wash["ref"] += "_carwash"
                car_wash.update(self.INTERMARCHE)

                apply_category(Categories.CAR_WASH, car_wash)

                yield car_wash

            yield item
