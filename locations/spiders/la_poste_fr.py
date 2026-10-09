from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.licenses import Licenses

# https://www.data.gouv.fr/datasets/liste-des-bureaux-de-poste-agences-postales-et-relais-poste
DATASET_URL = "https://data.laposte.fr/data-fair/api/v1/datasets/laposte-poincont2/lines"
PAGE_SIZE = 10000

# https://www.data.gouv.fr/datasets/67adf208fff16d427cc86a5e
# One row per site and per day over the next three months, keyed on the same
# identifier as the sites dataset.
CALENDAR_URL = "https://data.laposte.fr/data-fair/api/v1/datasets/tjwztt6h44ve52i7fln6rbxz/lines"
CALENDAR_FIELDS = ["plage_horaire_1", "plage_horaire_2", "plage_horaire_3", "plage_horaire_4"]
# Three weeks lets the most frequent slots of each weekday outvote a bank
# holiday or a one-off closure.
CALENDAR_WEEKS = 3

LA_POSTE = {"operator": "La Poste", "operator_wikidata": "Q373724"}

# Sites operated by La Poste or by a local authority on its behalf are post
# offices in their own right.
POST_OFFICES = {
    "Bureau de Poste",
    "Agence postale",
    "Agence postale communale",
    "Agence postale intercommunale",
}

# Shops (bakers, tobacconists, …) hosting a postal counter. Their own trade is
# not published, so they get amenity=yes like other post partners in ATP.
POST_PARTNERS = {
    "Agence postale ou Relais poste",
    "Point partenaire",
    "Relais poste",
}

COUNTRIES = {"FRANCE": "FR", "ANDORRE": "AD"}


class LaPosteFRSpider(Spider):
    name = "la_poste_fr"
    allowed_domains = ["data.laposte.fr"]
    # The portal's robots.txt is the stock data-fair template (identical to its
    # vendor's own opendata.koumoul.com) and blocks JSON endpoints from being
    # indexed. La Poste's terms of service list the API as a delivery channel
    # for the data, and data.gouv.fr publishes this URL as the dataset's file.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    dataset_attributes = Licenses.ETALAB2.value | {
        "source": "api",
        "attribution:name": "La Poste",
        "attribution:website": "https://data.laposte.fr/datasets/laposte-poincont2",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ref -> weekday -> Counter of that day's slots across the window
        self.slots = defaultdict(lambda: defaultdict(Counter))

    async def start(self) -> AsyncIterator[Request]:
        monday = date.today() + timedelta(days=7 - date.today().weekday())
        last_day = monday + timedelta(weeks=CALENDAR_WEEKS, days=-1)
        yield Request(
            url=f"{CALENDAR_URL}?size={PAGE_SIZE}&qs=date_calendrier:[{monday} TO {last_day}]"
            f"&select=identifiant,date_calendrier,{','.join(CALENDAR_FIELDS)}",
            callback=self.parse_calendar,
        )

    def parse_calendar(self, response: Response) -> Iterable[Request]:
        payload = response.json()
        for row in payload["results"]:
            if not row.get("identifiant") or not row.get("date_calendrier"):
                continue
            weekday = DAYS[date.fromisoformat(row["date_calendrier"]).weekday()]
            slots = tuple(row[field] for field in CALENDAR_FIELDS if row.get(field) and row[field] != "FERME")
            self.slots[row["identifiant"]][weekday][slots] += 1

        if next_page := payload.get("next"):
            yield Request(url=next_page, callback=self.parse_calendar)
        else:
            yield Request(url=f"{DATASET_URL}?size={PAGE_SIZE}")

    def opening_hours(self, ref: str) -> OpeningHours | None:
        # A site closed on every day of the window is shut for works or for
        # good, which says nothing about its usual hours.
        if not any(slots for day in self.slots.get(ref, {}).values() for slots in day):
            return None
        oh = OpeningHours()
        for day in DAYS:
            if not self.slots[ref][day]:
                continue
            slots = self.slots[ref][day].most_common(1)[0][0]
            if not slots:
                oh.set_closed(day)
            for slot in slots:
                oh.add_range(day, *slot.split("-"))
        return oh

    def parse(self, response: Response) -> Iterable[Any]:
        payload = response.json()

        for location in payload["results"]:
            # The dataset is refreshed monthly and its schema could shift, so
            # skip anything without the fields that make a location usable
            # rather than losing the rest of the page to a KeyError.
            if not location.get("identifiant_a"):
                self.crawler.stats.inc_value("atp/la_poste_fr/no_ref")
                continue
            if not location.get("latitude") or not location.get("longitude"):
                self.crawler.stats.inc_value("atp/la_poste_fr/no_coordinates")
                continue

            item = Feature()
            item["ref"] = location["identifiant_a"]
            item["branch"] = location.get("libelle_du_site")
            item["street_address"] = location.get("adresse")
            item["postcode"] = location.get("code_postal")
            item["city"] = location.get("localite")
            item["country"] = COUNTRIES.get(location.get("pays"))
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            # numero_de_telephone is always 3631, La Poste's national number.

            item["opening_hours"] = self.opening_hours(item["ref"])

            item["extras"]["ref:INSEE"] = location.get("code_insee")

            # An unrecognised or absent characteristic falls through to the
            # partner tagging, which claims less than amenity=post_office does.
            characteristic = location.get("caracteristique_du_site")
            if characteristic in POST_OFFICES:
                apply_category(Categories.POST_OFFICE, item)
                item.update(LA_POSTE)
            else:
                if characteristic not in POST_PARTNERS:
                    self.logger.error("Unexpected characteristic: {}".format(characteristic))
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
                item["extras"]["post_office:brand"] = "La Poste"
                item["extras"]["post_office:brand:wikidata"] = "Q373724"

            yield item

        if next_page := payload.get("next"):
            yield Request(url=next_page)
