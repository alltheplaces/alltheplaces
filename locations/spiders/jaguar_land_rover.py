from urllib.parse import quote

from scrapy import Request, Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.pipelines.state_clean_up import STATES

# Set of language and country as required for the "requestMarketLocale"
# parameter, then the actual ISO country code(s) required for
# country_iseadgg_centroids. These were gathered from the "market selector"
# pages at https://www.jaguar.com/retailer-locator/index.html and
# https://www.landrover.com/national-dealer-locator.html
COUNTRIES = {
    ("en", "au", "AU"),
    ("en", "bn", "BN"),
    ("en", "kh", "KH"),
    ("zh", "cn", "CN"),
    ("en", "hk", "HK"),
    ("en", "in", "IN"),
    ("en", "id", "ID"),
    ("jp", "jp", "JP"),
    ("ru", "kz", "KZ"),
    ("ko", "kr", "KR"),
    ("en", "la", "LA"),
    ("en", "my", "MY"),
    ("en", "mn", "MN"),
    ("en", "mm", "MM"),
    ("en", "nc", "NC"),
    ("fr", "fr", "FR"),
    ("en", "nz", "NZ"),
    ("en", "pk", "PK"),
    ("en", "ph", "PH"),
    ("en", "sg", "SG"),
    ("en", "lk", "LK"),
    ("zh", "tw", "TW"),
    ("en", "th", "TH"),
    ("en", "vn", "VN"),
    ("en", "al", "AL"),
    ("en", "am", "AM"),
    ("de", "at", "AT"),
    ("en", "az", "AZ"),
    ("fr", "be", "BE"),
    ("hr", "ba", "BA"),
    ("bg", "bg", "BG"),
    ("hr", "hr", "HR"),
    ("en", "cy", "CY"),
    ("tr", "cyl", "CY"),
    ("cs", "cz", "CZ"),
    ("da", "dk", "DK"),
    ("et", "ee", "EE"),
    ("fi", "fi", "FI"),
    ("fr", "fr", "FR"),
    ("en", "ge", "GE"),
    ("de", "de", "DE"),
    ("en", "gi", "GI"),
    ("el", "gr", "GR"),
    ("hu", "hu", "HU"),
    ("is", "is", "IS"),
    ("en", "ie", "IE"),
    ("it", "it", "IT"),
    ("en", "xk", "XK"),
    ("lv", "lv", "LV"),
    ("lt", "lt", "LT"),
    ("fr", "lu", "LU"),
    ("en", "mt", "MT"),
    ("ro", "md", "MD"),
    ("en", "me", "ME"),
    ("nl", "nl", "NL"),
    ("mk", "mk", "MK"),
    ("no", "no", "NO"),
    ("pl", "pl", "PL"),
    ("pt", "pt", "PT"),
    ("ro", "ro", "RO"),
    ("ru", "ru", "RU"),
    ("en", "rs", "RS"),
    ("sk", "sk", "SK"),
    ("sl", "si", "SI"),
    ("es", "es", "ES"),
    ("sv", "se", "SE"),
    ("fr", "ch", "CH"),
    ("tr", "tr", "TR"),
    ("uk", "ua", "UA"),
    ("en", "uk", "GB"),
    ("en", "gb", "GB"),
    ("fr", "dz", "DZ"),
    ("en", "ao", "AO"),
    ("en", "bh", "BH"),
    ("en", "eg", "EG"),
    ("en", "gh", "GH"),
    ("en", "iq", "IQ"),
    ("he", "il", "IL"),
    ("en", "ci", "CI"),
    ("en", "jo", "JO"),
    ("en", "ke", "KE"),
    ("en", "kw", "KW"),
    ("en", "lb", "LB"),
    ("en", "mu", "MU"),
    ("en", "ma", "MA"),
    ("en", "mz", "MZ"),
    ("en", "ng", "NG"),
    ("en", "om", "OM"),
    ("en", "ps", "PS"),
    ("en", "qa", "QA"),
    ("en", "sa", "SA"),
    ("en", "sn", "SN"),
    ("en", "za", "ZA"),
    ("en", "tz", "TZ"),
    ("fr", "tn", "TN"),
    ("en", "ae", "AE"),
    ("en", "ye", "YE"),
    ("en", "zm", "ZM"),
    ("en", "zw", "ZW"),
    ("en", "us", "US"),
    # ("en", "ca", "CA"),  # doesn't work with coordinate queries, see start_requests
    ("es", "cr", "CR"),
    ("es", "do", "DO"),
    ("es", "gt", "GT"),
    ("en", "jm", "JM"),
    ("es", "mx", "MX"),
    ("es", "pa", "PA"),
    ("en", "pr", "PR"),
    ("en", "tt", "TT"),
    ("es", "ar", "AR"),
    ("pt", "br", "BR"),
    ("es", "cl", "CL"),
    ("es", "co", "CO"),
    ("es", "ec", "EC"),
    ("es", "py", "PY"),
    ("es", "pe", "PE"),
    ("es", "uy", "UY"),
}


class JaguarLandRoverSpider(Spider):
    name = "jaguar_land_rover"

    def start_requests(self):
        for brand, brand_wikidata in {("Jaguar", "Q21170490"), ("Land Rover", "Q26777551")}:
            for language, country_jlr, country_iso in COUNTRIES:
                for lat, lng in country_iseadgg_centroids(country_iso, 458):
                    yield Request(
                        f"https://retailerlocator.jaguarlandrover.com/dealers?"
                        f"lat={lat}&"
                        f"lng={lng}&"
                        f"requestMarketLocale={language}_{country_jlr}&"
                        f"brand={quote(brand)}&"
                        f"radius=460&"
                        f"unitOfMeasure=Kilometers&"
                        f"country={country_jlr}",
                        cb_kwargs={"brand": brand, "brand_wikidata": brand_wikidata, "country": country_jlr},
                    )
            # The Canada site specifically doesn't work with the lat/lng
            # query above.
            for state in STATES["CA"]:
                yield Request(
                    f"https://retailerlocator.jaguarlandrover.com/dealers?"
                    f"region={state}&"
                    f"requestMarketLocale=en_ca&"
                    f"brand={quote(brand)}&"
                    f"radius=460&"
                    f"unitOfMeasure=Kilometers&"
                    f"country=ca",
                    cb_kwargs={"brand": brand, "brand_wikidata": brand_wikidata, "country": "ca"},
                )

    def add_contact(self, item, services, contact):
        all_contacts = set(filter(None, (service[contact] for service in services)))
        # If all of the (email/fax/phone) for each department is the same, only add that.
        if len(all_contacts) == 1:
            if contact in ("email", "phone"):
                item[contact] = all_contacts.pop()
            else:
                item["extras"][contact] = all_contacts.pop()
        # Otherwise, add each department separately.
        else:
            for service in services:
                item["extras"][service["type"] + ":" + contact] = service[contact]

    def parse(self, response, brand, brand_wikidata, country):
        js = response.json()
        if error_type := js.get("errorType"):
            if error_type == "com.connect_group.dealerlocator_lambda.response.NoResultsFound":
                # No results found. Not really an error. Ignore.
                return
            else:
                self.logger.error(js.get("errorMessage", error_type))

        for location in js.get("dealers", []):
            item = DictParser.parse(location)
            item["website"] = location["homePage"]

            # Only add brand tagging if it's a branded location.
            if location["authorisedRepairer"] or location["dealer"] or location["special"]:
                item["brand"] = brand
                item["brand_wikidata"] = brand_wikidata

            # "ciCode" seems to be the property most resembling an identifier,
            # but codes are reused between countries, and unfortunately some
            # locations list dealership and repairs separately.
            item["ref"] = country + ":" + location["ciCode"]

            self.add_contact(item, location["services"], "email")
            self.add_contact(item, location["services"], "fax")
            self.add_contact(item, location["services"], "phone")

            # Decide on a category. If it's a dealer, use that, then say if it
            # also offers repairs. Otherwise it's a car repair.
            if location["dealer"] or location["approvedPreOwned"]:
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no(Extras.CAR_REPAIR, item, location["authorisedRepairer"] or location["bodyshop"])
            elif location["authorisedRepairer"] or location["bodyshop"]:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            apply_yes_no(Extras.USED_CAR_SALES, item, location["approvedPreOwned"])

            yield item
