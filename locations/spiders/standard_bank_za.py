import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.pipelines.address_clean_up import clean_address

ZA_PROVINCES = [
    "Eastern Cape",
    "Free State",
    "Gauteng",
    "KwaZulu-Natal",
    "Limpopo",
    "Mpumalanga",
    "North West",
    "Northern Cape",
    "Western Cape",
]

ATM_TYPES_CASH_IN = {
    "AUTOCASH": False,
    "AUTOBANK": True,
    "AUTOPLUS": False,  # An option in the data, but no info about it on the website, does not appear to be used
}

CHAIN_LOCATIONS = {
    "7 Eleven": {"located_in": "7-Eleven", "located_in_wikidata": "Q259340"},
    "Boxer": {"located_in": "Boxer", "located_in_wikidata": "Q116586275"},
    "Bp": {"located_in": "BP", "located_in_wikidata": "Q152057"},
    "Caltex": {"located_in": "Caltex", "located_in_wikidata": "Q277470"},
    "Cambridge": {"located_in": "Cambridge Food", "located_in_wikidata": "Q129263104"},
    "Checkers": {"located_in": "Checkers", "located_in_wikidata": "Q5089126"},
    "Engen": {"located_in": "Engen", "located_in_wikidata": "Q3054251"},
    # 'Exel':         {"located_in": "", "located_in_wikidata": ""},
    # 'Foodworld':    {"located_in": "", "located_in_wikidata": ""}, # Essentialy defunct/bought-out brand
    # 'Friendly 7-11':{"located_in": "", "located_in_wikidata": ""},
    "Game": {"located_in": "Game", "located_in_wikidata": "Q129263113"},
    "Ok": {"located_in": "OK", "located_in_wikidata": "Q116520377"},
    "Pick 'n Pay": {"located_in": "Pick n Pay", "located_in_wikidata": "Q7190735"},
    "Puma Energy": {"located_in": "Puma", "located_in_wikidata": "Q7259769"},
    "Sasol": {"located_in": "Sasol", "located_in_wikidata": "Q905998"},
    # 'Score':        {"located_in": "", "located_in_wikidata": ""},
    "Shell": {"located_in": "Shell", "located_in_wikidata": "Q110716465"},
    "Shoprite": {"located_in": "Shoprite", "located_in_wikidata": "Q1857639"},
    "Spar": {"located_in": "Spar", "located_in_wikidata": "Q610492"},
    "Specsavers": {"located_in": "Specsavers", "located_in_wikidata": "Q2000610"},
    "Total": {"located_in": "Total", "located_in_wikidata": "Q154037"},
    "U - Save": {"located_in": "Usave", "located_in_wikidata": "Q115696368"},
    "Woolworths": {"located_in": "Woolworths", "located_in_wikidata": "Q8033997"},
    # 'Zenex':        {"located_in": "", "located_in_wikidata": ""},
}


class StandardBankZASpider(scrapy.Spider):
    name = "standard_bank_za"
    item_attributes = {"brand": "Standard Bank", "brand_wikidata": "Q1576610"}
    allowed_domains = ["digitalbanking.standardbank.co.za"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # HTTP 500 error for robots.txt
    start_urls = [
        f"https://digitalbanking.standardbank.co.za:8083/sbg-mobile/rest/Communications/geolocator/search?searchTerm={province}&language=en&country=South%20Africa"
        for province in ZA_PROVINCES
    ]

    def parse(self, response):
        data = response.json()
        for location in data["centers"]:
            item = DictParser.parse(location)
            item["lat"] = location["location"]["latitude"]
            item["lon"] = location["location"]["longitude"]
            item["state"] = location["location"]["nationalProv"]
            item["city"] = location["location"]["town"]
            item["postcode"] = location["location"]["postalCode"]
            item["country"] = location["location"]["country"]
            item["street"] = location["location"]["street"]
            item["street_address"] = clean_address(
                [location["location"]["shopNo"], location["location"]["shoppingCenter"], location["location"]["street"]]
            )
            item["branch"] = item.pop("name")
            item["opening_hours"] = self.parse_opening_hours(location)

            if location["locationType"] == "Branch":
                apply_category(Categories.BANK, item)
                yield from self.parse_branch(item, location)
            elif location["locationType"] == "ATM":
                apply_category(Categories.ATM, item)
                yield from self.parse_atm(item, location)
            else:
                self.logger.warning("Unknown category: {}".format(location["locationType"]))
                continue

    def parse_branch(self, item, location):
        item["ref"] = location.pop("centerNo")

        services = [service["name"] for service in location["services"]]
        # Possible services: 'Internet Kiosk', 'SBFC presence', 'Cashless Outlet', 'Forex', 'MoneyGram', 'Safe Custody',
        #    'MIE presence', 'Home Affairs Presence', 'Liberty Presence'

        apply_yes_no(Extras.MONEYGRAM, item, "MoneyGram" in services, True)

        apply_yes_no(Extras.WHEELCHAIR, item, location["wheelChairAccess"] == "YES")  # Value can be "UNKNOWN"
        apply_yes_no(
            Extras.BACKUP_GENERATOR, item, location.get("shoppingCenterGeneratorStatus") == "YES"
        )  # Value can be "UNKNOWN"

        yield item

    def parse_atm(self, item, location):
        item["ref"] = location.pop("gresId")

        # Despite being a list, it appears to always have either 0 or 1 elements
        if len(location["atms"]) > 0:
            apply_yes_no(Extras.CASH_IN, item, ATM_TYPES_CASH_IN[location["atms"][0]["atmType"]], False)
            if location["atms"][0]["chain"] in CHAIN_LOCATIONS:
                item.update(CHAIN_LOCATIONS[location["atms"][0]["chain"]])
            else:
                item["located_in"] = location["atms"][0]["chain"]
            # location["atms"]["typeOfSite"] does not appear to be useful

        yield item

    def parse_opening_hours(self, location):
        oh = OpeningHours()
        if location["operatingHours"] == []:
            return None
        for line in location["operatingHours"]:
            try:
                day_time = line["hours"].split(":")
                # Slight hack so that the later splitting on dash works
                day_time[1] = day_time[1].lower().replace("only", "").strip()
                if day_time[1].strip().lower() == "closed":
                    day_time[1] = "closed-closed"
                if day_time[0].strip().title() in DAYS_3_LETTERS:
                    oh.add_range(
                        day_time[0], day_time[1].split("-")[0].strip(), day_time[1].split("-")[1].strip(), "%HH%M"
                    )
                elif "&" in day_time[0]:
                    for day in day_time[0].split("&"):
                        try:
                            for times in day_time[1].split("&"):
                                times = times.strip()
                                oh.add_range(day, times.split("-")[0].strip(), times.split("-")[1].strip(), "%HH%M")
                        except ValueError:
                            pass
                elif "-" in day_time[0]:
                    try:
                        for times in day_time[1].split("&"):
                            times = times.strip()
                            oh.add_days_range(
                                oh.days_in_day_range(
                                    [day_time[0].split("-")[0].strip(), day_time[0].split("-")[1].strip()]
                                ),
                                times.split("-")[0].strip(),
                                times.split("-")[1].strip(),
                                "%HH%M",
                            )
                    except ValueError:
                        pass
            except:
                pass
        return oh.as_opening_hours()
