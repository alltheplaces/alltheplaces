import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaSpider(scrapy.Spider):
    name = "mazda"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    countries = {
        "at": "https://www.mazda.at/formular/haendlersuche/",
        "be": "https://fr.mazda.be/formulaires/rechercher-un-concessionnaire/",
        "ch": "https://de.mazda.ch/forms/handler/",
        "cz": "https://www.mazda.cz/formulae/prodejci-a-opravci/",
        "de": "https://www.mazda.de/formular/haendlersuche/",
        "dk": "https://www.mazda.dk/formularer/find-forhandler/",
        "es": "https://www.mazda.es/formularios/localiza-tu-concesionario/",
        "fr": "https://www.mazda.fr/formulaire/recherchez-un-concessionnaire/",
        "hr": "https://www.mazda.hr/obrasci/pretraga-partnera/",
        "hu": "https://www.mazda.hu/forms/markakereskedk/",
        "ie": "https://www.mazda.ie/forms/find-a-dealer/",
        "it": "https://www.mazda.it/forms/trova-un-concessionario/",
        "pl": "https://www.mazda.pl/forms/znajdz-dealera/",
        "pt": "https://www.mazda.pt/formularios/localizar-um-concessionario/",
        "nl": "https://www.mazda.nl/forms/vind-een-dealer/",
        "no": "https://www.mazda.no/forms/finn-forhandler/",
        "ro": "https://www.mazda.ro/formulare/caut-un-dealer/",
        "se": "https://www.mazda.se/forms/hitta-aterforsaljare/",
        "si": "https://www.mazda.si/obrazci/trgovska-mreza/",
        "sk": "https://www.mazda.sk/formulare/predajcovia-a-servis/",
        "tr": "https://www.mazda.com.tr/formlar/bayi-bulun/",
        "uk": "https://www.mazda.co.uk/forms/find-a-dealer/",
    }

    def start_requests(self):
        for country in self.countries:
            if country == "uk":
                yield JsonRequest(url=f"https://www.mazda.co.{country}/api/dealers", cb_kwargs=dict(country=country))
            elif country == "tr":
                yield JsonRequest(url=f"https://www.mazda.com.{country}/api/dealers", cb_kwargs=dict(country=country))
            else:
                yield JsonRequest(url=f"https://www.mazda.{country}/api/dealers", cb_kwargs=dict(country=country))

    def parse(self, response, **kwargs):
        for dealer in response.json()["data"]["dealers"]:
            item = DictParser.parse(dealer)
            item["ref"] = dealer["dealerCode"]
            item["phone"] = dealer["phoneNumber"]["international"]
            if not dealer.get("contact").get("website"):
                item["website"] = self.countries[kwargs["country"]]
            item["website"] = item["website"].replace(" ", "").replace("\t", "")

            services = [service.get("name", "").lower() for service in dealer.get("services", [])]
            category_type = "car sales"
            if "car sales" in services:
                apply_category(Categories.SHOP_CAR, item)
            else:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
                category_type = "car repair"
            if "parts sales" in services:
                item["extras"]["service"] = "dealer;repair;parts"
            elif "car repair" in services:
                item["extras"]["service"] = "dealer;repair"
            apply_yes_no("second_hand", item, "approved used-car services" in services)

            item["opening_hours"] = OpeningHours()
            if timing := dealer.get("openingHours"):
                for rule in timing:
                    if rule.get("type", "").lower() == category_type:
                        if day := sanitise_day(rule.get("dayOfWeek")):
                            item["opening_hours"].add_range(day, rule["from"], rule["to"])
            yield item
