from typing import ClassVar

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.country_utils import get_locale
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.storefinders.woosmap import WoosmapSpider


class AccorSpider(WoosmapSpider):
    name = "accor"
    key = "accor-prod-woos"
    origin = "https://accor.com"

    # Languages that https://all.accor.com/ hotel pages are published in
    # (i.e. valid "index.<lang>.shtml" suffixes). A country whose language
    # is not in this set falls back to English.
    SUPPORTED_WEBSITE_LANGUAGES: ClassVar[set[str]] = {
        "ar",
        "de",
        "en",
        "es",
        "fr",
        "id",
        "it",
        "ja",
        "ko",
        "nl",
        "pl",
        "pt",
        "pt-br",
        "ru",
        "th",
        "tr",
        "zh",
    }
    # Countries where the language code returned by country_utils.get_locale()
    # does not match the locale code used by all.accor.com.
    WEBSITE_LANGUAGE_OVERRIDES: ClassVar[dict[str, str]] = {"BR": "pt-br"}

    brand_mapping: ClassVar[dict[str, dict[str, str] | None]] = {
        "SUI": {"brand": "Novotel", "brand_wikidata": "Q420545"},
        "NOV": {"brand": "Novotel", "brand_wikidata": "Q420545"},
        "NOL": {"brand": "Novotel", "brand_wikidata": "Q420545"},
        "IBS": {"brand": "Ibis Styles", "brand_wikidata": "Q3147425"},
        "PUL": {"brand": "Pullman", "brand_wikidata": "Q3410757"},
        "IBH": {"brand": "Ibis", "brand_wikidata": "Q920166"},
        "IBB": {"brand": "Ibis Budget", "brand_wikidata": "Q1458135"},
        "ETP": {"brand": "Ibis Budget", "brand_wikidata": "Q1458135"},
        "SOL": {"brand": "Sofitel", "brand_wikidata": "Q749431"},
        "MOV": {"brand": "Mövenpick", "brand_wikidata": "Q691162"},
        "MER": {"brand": "Mercure", "brand_wikidata": "Q1709809"},
        "BME": {"brand": "Mercure", "brand_wikidata": "Q1709809"},
        "ADG": {"brand": "Adagio", "brand_wikidata": "Q2823880"},
        "ADA": {"brand": "Adagio", "brand_wikidata": "Q2823880"},
        "ADP": {"brand": "Adagio", "brand_wikidata": "Q2823880"},
        "MSH": {"brand": "Mama Shelter", "brand_wikidata": "Q12716714"},
        "FAI": {"brand": "Fairmont", "brand_wikidata": "Q1393345"},
        "MEI": {"brand": "Mercure", "brand_wikidata": "Q1709809"},
        "MEL": {"brand": "Mercure", "brand_wikidata": "Q1709809"},
        "SEB": {"brand": "The Sebel", "brand_wikidata": "Q110888248"},
        "HOF": {"brand": "hotelF1", "brand_wikidata": "Q1630895"},
        "MGA": {"brand": "MGallery", "brand_wikidata": "Q25419207"},
        "MGS": {"brand": "MGallery", "brand_wikidata": "Q25419207"},
        "SOF": {"brand": "Sofitel", "brand_wikidata": "Q749431"},
        "SWI": {"brand": "Swissôtel", "brand_wikidata": "Q1635974"},
        "SWL": {"brand": "Swissôtel", "brand_wikidata": "Q1635974"},
        "BAN": {"brand": "Banyan Tree", "brand_wikidata": "Q807019"},
        "RIX": {"brand": "Rixos Hotels", "brand_wikidata": "Q6075716"},
        "TWF": {"brand": "25hours Hotels", "brand_wikidata": "Q47503819"},
        "RAF": {"brand": "Raffles", "brand_wikidata": "Q4306661"},
        "JOE": {"brand": "JO&JOE", "brand_wikidata": "Q84600897"},
        "MTA": {"brand": "Mantra Hotels", "brand_wikidata": "Q110936540"},
        "BKF": {"brand": "BreakFree Hotels", "brand_wikidata": "Q110936724"},
        "PEP": {"brand": "Peppers Hotels", "brand_wikidata": "Q110936677"},
        "MOD": {"brand": "Mondrian Hotel", "brand_wikidata": "Q6898825"},
        "21C": {"brand": "21c Museum Hotels", "brand_wikidata": "Q4631016"},
        "ANG": {"brand": "Angsana", "brand_wikidata": "Q115489061"},
        "ART": {"brand": "Art Series", "brand_wikidata": "Q115489062"},
        "DHA": {"brand": "Dhawa"},
        "GRE": {"brand": "greet", "brand_wikidata": "Q115489066"},
        "MTS": {"brand": "Mantis"},
        "SO": {"brand": "SO/", "brand_wikidata": "Q115489077"},
        "SOU": {"brand": "Handwritten Collection"},
        "TRI": {"brand": "TRIBE", "brand_wikidata": "Q113694525"},
        # Not branded but managed by Accor
        "SAM": None,
        # TODO:
        # Table with brands by Accor: https://group.accor.com/en/sitemap
        # "ASE": 1,
        # "CAS": 3,
        # "DEL": 1,
        # "FAE": 1,
        # "GAR": 1,
        # "HOM": 2,
        # "HOX": 1,
        # "HYD": 2,
        # "MOL": 2,
        # "SLS": 7,
        # "TST": 6,
    }

    # Woosmap "tags" that map cleanly onto an OSM extras tag. Absence of a
    # tag is not treated as a "no" since Woosmap's tagging is not known to
    # be exhaustive (apply_yes_no's default apply_positive_only=True skips
    # the negative case for us).
    TAG_EXTRAS: ClassVar[dict[str, Extras]] = {
        "wifi": Extras.WIFI,
        "air_conditioning": Extras.AIR_CONDITIONING,
        "parking": Extras.PARKING,
        "wheelchair_access": Extras.WHEELCHAIR,
        "pool": Extras.SWIMMING_POOL,
        "pet": Extras.PETS_ALLOWED,
    }
    # Named entries in a hotel page's schema.org amenityFeature list that map
    # onto an OSM extras tag.
    AMENITY_EXTRAS: ClassVar[dict[str, Extras]] = {
        "Bar": Extras.BAR,
        "Breakfast": Extras.BREAKFAST,
    }

    def parse_item(self, item, feature, **kwargs):
        if "COMING SOON" in item["name"].upper():
            return
        brand_id = feature["properties"]["types"][0]
        if match := self.brand_mapping.get(brand_id):
            item.update(match)
        else:
            self.crawler.stats.inc_value(f"atp/accor/unknown_brand/{brand_id}")
        item["addr_full"] = item.pop("street_address")
        item["website"] = (
            f"https://all.accor.com/hotel/{item['ref']}/index.{self.website_language(item['country'])}.shtml"
        )

        if stars := feature["properties"]["user_properties"].get("localRating"):
            item["extras"]["stars"] = str(stars).removesuffix(".0")

        tags = feature["properties"].get("tags", [])
        for tag, extra in self.TAG_EXTRAS.items():
            apply_yes_no(extra, item, tag in tags)
        if "non_smoking" in tags:
            # Explicitly asserted by the source, unlike the tags above whose
            # absence doesn't tell us anything either way.
            apply_yes_no(Extras.SMOKING, item, False, apply_positive_only=False)

        apply_category(Categories.HOTEL, item)

        # Phone, email and a couple of amenities are only available on the
        # hotel's own page, not in the Woosmap feed, so fetch it too. Always
        # use the English page for this regardless of item["website"]'s
        # language: phone/email don't vary by language, but the amenity
        # names we match on (self.AMENITY_EXTRAS) are translated on other
        # locales, e.g. "Breakfast" becomes "Petit-déjeuner" on the French
        # page. Fall back to yielding what we already have if the request
        # fails.
        detail_url = f"https://all.accor.com/hotel/{item['ref']}/index.en.shtml"
        yield Request(detail_url, callback=self.parse_hotel_page, cb_kwargs={"item": item}, errback=self.failed)

    def website_language(self, country: str | None) -> str:
        language = self.WEBSITE_LANGUAGE_OVERRIDES.get(country)
        if not language and country:
            locale = get_locale(country)
            language = locale.split("-")[0] if locale else None
        return language if language in self.SUPPORTED_WEBSITE_LANGUAGES else "en"

    def parse_hotel_page(self, response: Response, item: Feature):
        if ld := LinkedDataParser.find_linked_data(response, "Hotel"):
            if phone := LinkedDataParser.get_case_insensitive(ld, "telephone"):
                item["phone"] = phone
            if email := LinkedDataParser.get_case_insensitive(ld, "email"):
                item["email"] = email
            amenity_features = ld.get("amenityFeature") or []
            if isinstance(amenity_features, dict):
                # schema.org allows a single-valued multi-value property to
                # be serialised as a lone object instead of a one-item list.
                amenity_features = [amenity_features]
            amenities = {a.get("name") for a in amenity_features if str(a.get("value")).lower() == "true"}
            for name, extra in self.AMENITY_EXTRAS.items():
                apply_yes_no(extra, item, name in amenities)
        yield item

    def failed(self, failure):
        yield failure.request.cb_kwargs["item"]
