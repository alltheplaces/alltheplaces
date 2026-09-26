import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FonciaFRSpider(Spider):
    name = "foncia_fr"
    item_attributes = {"brand": "Foncia", "brand_wikidata": "Q1435638"}
    # The agence-immobiliere.xml sitemap is stale (dead agencies, missing new
    # ones, online-only "LOC 100% en ligne" offices), so follow the store
    # finder's own department search instead. Agency pages are not used as
    # their structured data opening hours drop lunch breaks and some days.
    start_urls = ["https://fr.foncia.com/agence-immobiliere/toutes-les-agences-par-departement"]
    api_url = "https://fnc-api.prod.fonciatech.net/agences/agences/"

    def parse(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        for slug in response.xpath("//a/@href").re(r"/agence-immobiliere/agences-immobilieres/([^/?#]+)$"):
            yield JsonRequest(
                url=self.api_url + "search",
                data={"page": 1, "size": 150, "filters": {"activites": [], "slug": slug}},
                callback=self.parse_agencies,
            )

    def parse_agencies(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        for agency in response.json()["agences"]:
            yield JsonRequest(url=self.api_url + agency["numeroAgence"], callback=self.parse_agency)

    def parse_agency(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        agency = response.json()
        if agency.get("agenceVirtuelle"):
            return

        location = agency["localisation"]
        item = Feature()
        item["ref"] = agency["numeroAgence"]
        item["street_address"] = merge_address_lines([location["adresse1"], location["adresse2"]])
        item["postcode"] = location["codePostal"]
        item["city"] = location["ville"]["libelle"]
        item["lat"] = location["geoPoint"]["lat"]
        item["lon"] = location["geoPoint"]["lon"]
        item["phone"] = agency["tel"]
        item["email"] = agency["mail"]
        item["image"] = agency["urlPhoto"]
        item["website"] = "https://fr.foncia.com" + agency["canonicalUrl"]

        if re.match(r"foncia\b", agency["nom"], flags=re.IGNORECASE):
            item["branch"] = agency["nom"][len("foncia") :].strip(" -")
        else:
            item["name"] = agency["nom"]

        item["opening_hours"] = OpeningHours()
        for rule in agency.get("horaires") or []:
            times = [rule[key] for key in ("startAM", "endAM", "startPM", "endPM") if rule.get(key)]
            ranges = " ".join(f"{start}-{end}" for start, end in zip(times[::2], times[1::2])).replace("h", ":")
            item["opening_hours"].add_ranges_from_string(
                f"{rule['days']} {ranges}", days=DAYS_FR, delimiters=DELIMITERS_FR
            )

        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
