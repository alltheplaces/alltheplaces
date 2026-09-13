import json
import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.licenses import Licenses

# https://www.data.gouv.fr/datasets/service-public-gouv-fr-annuaire-de-ladministration-base-de-donnees-locales
# The export endpoint returns every matching record in one response, so there
# is no pagination to walk (the records endpoint caps out at 10000 anyway).
DATASET_URL = (
    "https://api-lannuaire.service-public.gouv.fr/api/explore/v2.1/catalog/datasets"
    "/api-lannuaire-administration/exports/json?where=pivot%20like%20%22france_travail%22"
    "&select=id,nom,pivot,adresse,plage_ouverture,siret"
)


class FranceTravailFRSpider(Spider):
    name = "france_travail_fr"
    item_attributes = {"brand": "France Travail", "brand_wikidata": "Q8901192"}
    allowed_domains = ["api-lannuaire.service-public.gouv.fr"]
    # The portal's robots.txt is the stock Opendatasoft template and blocks
    # /api/ from indexing. data.gouv.fr publishes this API as the dataset's
    # official access channel, under the Etalab 2.0 licence.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    dataset_attributes = Licenses.ETALAB2.value | {
        "source": "api",
        "attribution:name": "Direction de l'information légale et administrative (DILA)",
        "attribution:website": "https://lannuaire.service-public.gouv.fr/",
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url=DATASET_URL)

    def parse(self, response: Response) -> Iterable[Any]:
        for location in response.json():
            # Several fields are JSON documents embedded in strings.
            pivots = json.loads(location["pivot"] or "[]")
            if not any(pivot["type_service_local"] == "france_travail" for pivot in pivots):
                continue

            # "Adresse postale" entries are PO boxes and carry no coordinates.
            addresses = [a for a in json.loads(location["adresse"] or "[]") if a["type_adresse"] == "Adresse"]
            if not addresses or not addresses[0].get("latitude"):
                self.crawler.stats.inc_value("atp/france_travail_fr/no_coordinates")
                continue
            address = addresses[0]

            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = re.sub(r"^(Agence|Relai)\b.*?France Travail\s*", "", location["nom"])
            item["street_address"] = ", ".join(
                filter(None, [address["complement1"], address["complement2"], address["numero_voie"]])
            )
            item["postcode"] = address["code_postal"]
            item["city"] = address["nom_commune"]
            item["country"] = "FR"
            item["lat"] = address["latitude"]
            item["lon"] = address["longitude"]
            # The only telephone and website given are the national hotline
            # (3949) and francetravail.fr, shared by every office.
            item["extras"]["ref:FR:SIRET"] = location["siret"]

            apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
            item["opening_hours"] = self.parse_opening_hours(json.loads(location["plage_ouverture"] or "[]"))

            yield item

    def parse_opening_hours(self, ranges: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for day_range in ranges:
            start = sanitise_day(day_range["nom_jour_debut"], DAYS_FR)
            # A handful of records leave the end of the range empty.
            end = sanitise_day(day_range["nom_jour_fin"], DAYS_FR) or start
            if not start:
                self.crawler.stats.inc_value("atp/france_travail_fr/unparsed_days")
                continue
            first, last = DAYS.index(start), DAYS.index(end)
            days = DAYS[first : last + 1] if first <= last else DAYS[first:] + DAYS[: last + 1]
            for slot in ("1", "2"):
                oh.add_days_range(
                    days,
                    day_range[f"valeur_heure_debut_{slot}"],
                    day_range[f"valeur_heure_fin_{slot}"],
                    time_format="%H:%M:%S",
                )
        return oh
