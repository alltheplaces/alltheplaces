import scrapy
from scrapy import Request

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class IntermarcheSpider(scrapy.Spider):
    name = "intermarche"
    allowed_domains = ["intermarche.com"]
    INTERMARCHE_SUPER = {"brand": "Intermarché Super", "brand_wikidata": "Q3153200"}
    INTERMARCHE_CONTACT = {"brand": "Intermarché Contact", "brand_wikidata": "Q3153200"}
    INTERMARCHE_EXPRESS = {
        "brand": "Intermarché Express",
        "brand_wikidata": "Q98278043",
    }
    INTERMARCHE_HYPER = {"brand": "Intermarché Hyper", "brand_wikidata": "Q3153200"}
    item_attributes = {"country": "FR"}

    def start_requests(self):
        yield Request(
            url="https://www.intermarche.com/api/service/pdvs/v4/pdvs/zone?r=10000&lat=43.646715&lon=1.433066&min=10000",
            headers={"x-red-version": "3", "x-red-device": "red_fo_desktop"},
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

            if place.get("modelLabel") in [
                "SUPER ALIMENTAIRE",
                "SUPER GENERALISTE",
            ]:  # TODO: Difference?
                item.update(self.INTERMARCHE_SUPER)
                item["brand"] = place["modelLabel"]
            elif place.get("modelLabel") == "CONTACT":
                item.update(self.INTERMARCHE_CONTACT)
            elif place.get("modelLabel") == "EXPRESS":
                item.update(self.INTERMARCHE_EXPRESS)
            elif place.get("modelLabel") == "HYPER":
                item.update(self.INTERMARCHE_HYPER)
            elif place.get("modelLabel") == "Réservé Soignants":
                continue  # Seems to be a variant of other items
            elif place.get("modelLabel") == "Retrait La Poste":
                item["brand"] = place["modelLabel"]
                # TODO: What is this?

            yield item
