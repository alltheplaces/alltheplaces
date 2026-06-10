import re

import chompjs
from scrapy import Spider

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.spiders.colruyt import ColruytSpider
from locations.spiders.e_leclerc import ELeclercSpider
from locations.spiders.shell import ShellSpider
from locations.spiders.total_energies import TotalEnergiesSpider


class BilLUSpider(Spider):
    name = "bil_lu"
    item_attributes = {"brand": "BIL", "brand_wikidata": "Q2883404"}
    LOCATED_IN_MAPPINGS = [
        (["Shell"], ShellSpider.item_attributes),
        (["Station Total"], TotalEnergiesSpider.BRANDS["tot"]),
        (["Cactus"], {"brand": "Cactus", "brand_wikidata": "Q466918"}),
        (["E.Leclerc"], ELeclercSpider.item_attributes),
        (["Match"], {"brand": "Match", "brand_wikidata": "Q513977"}),
        (["Colruyt"], ColruytSpider.item_attributes),
        (["Kinepolis"], {"brand": "Kinepolis", "brand_wikidata": "Q1741993"}),
        (["Aéroport de Luxembourg"], {"name": "Aéroport de Luxembourg", "brand_wikidata": "Q872186"}),
    ]
    # Branch and ATM data is hardcoded into the JS bundle rendering the map on
    # https://www.bil.com/fr/particuliers/Pages/Contact.aspx ("var _g = [...]").
    start_urls = ["https://www.bil.com/Style%20Library/BIL/Scripts/maps.js"]

    def parse(self, response):
        js = response.text
        js = js[js.index("var _g = [") :]
        # The source contains \xE9-style escapes, which are not valid JSON.
        js = re.sub(r"\\x([0-9a-fA-F]{2})", r"\\u00\g<1>", js)
        for location in chompjs.parse_js_object(js):
            # Unquoted JS keys keep their unicode escapes as literal text, eg "Localité".
            location = {
                re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), key): value
                for key, value in location.items()
            }

            item = Feature()
            # "Nom" can have a parenthesised description on a second line, eg for the airport ATMs.
            item["ref"] = item["branch"] = location["Nom"].split("\n")[0].strip()
            item["street_address"] = location["Ligne-dadresse-1"]
            item["city"] = location["Localité"]
            item["postcode"] = str(location["Code postal"])
            item["country"] = location["Pays/Région"]
            item["lat"] = location["Latitude"]
            item["lon"] = location["Longitude"]
            item["phone"] = location["telephone"]
            item["opening_hours"] = self.parse_opening_hours(location)

            apply_yes_no(
                Extras.WHEELCHAIR, item, location["Accessible-en-fauteuil-roulant"] == "oui", apply_positive_only=False
            )

            # "Retrait" (withdrawal) is eg "EUR, USD, GBP, CHF, 24/7" or "non".
            if location["Typeagence"] == "Agence":
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, location["Retrait"] != "non", apply_positive_only=False)
            else:
                apply_category(Categories.ATM, item)
                apply_yes_no(Extras.CASH_IN, item, location["Versement-EUR"] == "oui", apply_positive_only=False)
                for currency in re.findall(r"\b(EUR|USD|GBP|CHF)\b", location["Retrait"]):
                    item["extras"][f"currency:{currency}"] = "yes"
                item["located_in"], item["located_in_wikidata"] = extract_located_in(
                    item["branch"], self.LOCATED_IN_MAPPINGS, self
                )

            yield item

    @staticmethod
    def parse_opening_hours(location):
        day_hours = {DAYS_FR[key]: value for key, value in location.items() if key in DAYS_FR}
        if day_hours and all(value == "24/7" for value in day_hours.values()):
            return "24/7"
        oh = OpeningHours()
        for day, hours in day_hours.items():
            if hours == "24/7":
                oh.add_range(day, "00:00", "24:00")
                continue
            # Eg "09h00-12h00, 13h30-17h00" for branches, "04:00-24:00" for ATMs.
            for rule in hours.split(","):
                if times := re.match(r"(\d{1,2})[h:](\d{2})\s*-\s*(\d{1,2})[h:](\d{2})", rule.strip()):
                    oh.add_range(day, f"{times.group(1)}:{times.group(2)}", f"{times.group(3)}:{times.group(4)}")
        return oh
