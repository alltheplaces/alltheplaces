import re

from scrapy import Request, Spider

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours, day_range
from locations.items import Feature
from locations.spiders.carrefour_fr import CARREFOUR_SUPERMARKET
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.fairmont import FairmontSpider
from locations.spiders.ikea import IkeaSpider
from locations.spiders.total_energies import TotalEnergiesSpider
from locations.spiders.vodafone_de import VODAFONE_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT

API_URL = "https://www.nbk.com/.rest/nbk/locations?lang={lang}&path={site}"
ARABIC_TEXT = re.compile(r"[؀-ۿ]")


class NationalBankOfKuwaitSpider(Spider):
    name = "national_bank_of_kuwait"
    item_attributes = {"brand": "National Bank of Kuwait", "brand_wikidata": "Q4045072"}
    # Venues hosting offsite machines, eg "The Avenues - IKEA - ATM" or "Circle K Almaza".
    LOCATED_IN_MAPPINGS = [
        (["IKEA"], IkeaSpider.item_attributes),
        (["Carrefour"], CARREFOUR_SUPERMARKET),
        (["Lulu Hypermarket"], {"brand": "Lulu Hypermarket", "brand_wikidata": "Q6702930"}),
        (["Four Points by Sheraton"], {"brand": "Four Points by Sheraton", "brand_wikidata": "Q1439966"}),
        (["Sheraton"], {"brand": "Sheraton", "brand_wikidata": "Q634831"}),
        (["Four Seasons"], {"brand": "Four Seasons", "brand_wikidata": "Q1424786"}),
        (["Hilton"], {"brand": "Hilton", "brand_wikidata": "Q598884"}),
        (["Marriott"], {"brand": "Marriott", "brand_wikidata": "Q3918608"}),
        (["Fairmont"], FairmontSpider.FAIRMONT),
        (["Westin"], {"brand": "The Westin", "brand_wikidata": "Q1969162"}),
        (["Vodafone"], VODAFONE_SHARED_ATTRIBUTES),
        (["Circle K"], CircleKSpider.CIRCLE_K),
        (["Mobil"], {"brand": "Mobil", "brand_wikidata": "Q109676002"}),
        (["Total"], TotalEnergiesSpider.BRANDS["tot"]),
        (["Eni"], {"brand": "Eni", "brand_wikidata": "Q565594"}),
        (["Misr Petroleum"], {"brand": "Misr Petroleum", "brand_wikidata": "Q10982617"}),
    ]
    # The bank's WAF blocks requests without a full browser user agent.
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    # API backing the map on https://www.nbk.com/<site>/find-us.html, one site per country.
    SITES = {
        "kuwait": "KW",
        "egypt": "EG",
        "uae": "AE",
        "ksa": "SA",
        "bahrain": "BH",
        "jordan": "JO",
        "lebanon": "LB",
        "london": "GB",
        "iraq": "IQ",
    }

    async def start(self):
        for site, country in self.SITES.items():
            yield Request(API_URL.format(lang="en", site=site), cb_kwargs={"country": country, "site": site})

    def parse(self, response, country, site):
        items = {}
        for location in response.xpath("//BranchItem"):
            item = Feature()
            item["ref"] = location.xpath("id/text()").get()
            item["lat"] = location.xpath("latitudes/text()").get()
            item["lon"] = location.xpath("longitudes/text()").get()
            item["addr_full"] = location.xpath("address/text()").get()
            item["city"] = location.xpath("AreasList/Areaitem/Atitle/text()").get()
            item["country"] = country
            item["phone"] = location.xpath("phone_no/text()").get()
            item["extras"]["fax"] = location.xpath("fax_no/text()").get()

            name = location.xpath("name/text()").get("").strip()
            facilities = location.xpath("FacilitiesList/Facilityitem/Ftitle/text()").getall()
            # The "pinImage" branch/ATM marker is unreliable (in Egypt most offsite ATMs carry the
            # branch marker), so classify by the facility list instead.
            is_branch = "Branch" in facilities or ("ATM" not in facilities and "branch" in name.lower())
            if is_branch:
                item["branch"] = name
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, "ATM" in facilities)
            else:
                # Machines are named after their venue or host branch, eg "The Avenues - IKEA - ATM"
                # or "Madinaty Branch - ATM II".
                item["branch"] = re.sub(r"\s*-?\s*\b(ATM|ITM|CDM)\b[^-]*$", "", name)
                apply_category(Categories.ATM, item)
                item["located_in"], item["located_in_wikidata"] = extract_located_in(
                    name, self.LOCATED_IN_MAPPINGS, self
                )
            item["opening_hours"] = self.parse_opening_hours(
                location.xpath("workingHoursLabels/text()").get(), is_branch
            )
            apply_yes_no(Extras.CASH_IN, item, "CDM" in facilities or "Cash Deposit" in facilities)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Through" in facilities or "Drive-Through" in facilities)

            items[item["ref"]] = item

        # The same locations are also published in Arabic, the local language everywhere but London.
        yield Request(
            API_URL.format(lang="ar", site=site),
            callback=self.parse_arabic,
            cb_kwargs={"items": items},
            errback=self.parse_arabic_failed,
        )

    def parse_arabic(self, response, items):
        for location in response.xpath("//BranchItem"):
            item = items.get(location.xpath("id/text()").get())
            if item is None:
                continue
            name = location.xpath("name/text()").get("").strip()
            if ARABIC_TEXT.search(name):
                # Machine names carry a descriptive suffix, eg "جهاز سحب آلي" (ATM).
                name = re.sub(r"\s*-\s*جهاز\s[^-]*$", "", name)
                item["extras"]["branch:en"] = item["branch"]
                item["branch"] = item["extras"]["branch:ar"] = name
            address = location.xpath("address/text()").get()
            if address and ARABIC_TEXT.search(address):
                item["extras"]["addr:full:en"] = item["addr_full"]
                item["addr_full"] = item["extras"]["addr:full:ar"] = address
        yield from items.values()

    def parse_arabic_failed(self, failure):
        # Don't lose a whole country over the Arabic feed: yield the English-only items.
        yield from failure.request.cb_kwargs["items"].values()

    @staticmethod
    def parse_opening_hours(label, is_branch):
        if not label:
            return None
        if label.strip().lower() == "24 hours":
            return "24/7"
        oh = OpeningHours()
        # Eg "8:30 AM - 3 PM | Sunday - Thursday", "9 AM - 1 PM | Sunday - Thursday,5 PM - 7 PM | Sunday - Wednesday",
        # "09.30 AM to 04.30 PM", or just "9 AM - 8:30 PM" for machines available daily.
        for rule in label.replace("–", "-").replace(" to ", " - ").split(","):
            if match := re.fullmatch(
                r"(\d{1,2})(?:[:.](\d{2}))?\s*([AP]M)\s*-\s*(\d{1,2})(?:[:.](\d{2}))?\s*([AP]M)"
                r"(?:\s*\|\s*(\w+)(?:\s*-\s*(\w+))?)?",
                rule.strip(),
                re.IGNORECASE,
            ):
                open_h, open_m, open_ap, close_h, close_m, close_ap, day_start, day_end = match.groups()
                try:
                    if day_start and day_end:
                        days = day_range(day_start, day_end)
                    elif day_start:
                        days = [day_start]
                    elif not is_branch:
                        # Machine hours without days, eg mall opening times, apply daily.
                        days = DAYS
                    else:
                        # Branch hours without days (most Egypt branches): the open days are unknown,
                        # so don't guess.
                        continue
                    oh.add_days_range(
                        days,
                        f"{open_h}:{open_m or '00'} {open_ap.upper()}",
                        f"{close_h}:{close_m or '00'} {close_ap.upper()}",
                        "%I:%M %p",
                    )
                except ValueError:
                    # Eg an unrecognised day word or a nonsense time: skip the rule, keep the item.
                    continue
        return oh
