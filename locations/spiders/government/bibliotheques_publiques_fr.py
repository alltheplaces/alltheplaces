import re
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.licenses import Licenses

# https://www.data.gouv.fr/datasets/adresses-des-bibliotheques-publiques-2
DATASET_URL = "https://www.data.gouv.fr/api/1/datasets/r/e3588487-4732-4b6c-ab12-72d75d7f522f"
WEBSITE_REGEX = re.compile(r"https?://(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}(?:/\S*)?$", re.IGNORECASE)


class BibliothequesPubliquesFRSpider(Spider):
    name = "bibliotheques_publiques_fr"
    allowed_domains = ["data.gouv.fr"]
    # data.gouv.fr publishes this stable resource URL as the dataset's file,
    # but its robots.txt blocks automated access to the /api/1/datasets/r/ path.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    dataset_attributes = Licenses.ETALAB2.value | {
        "source": "api",
        "attribution:name": "Ministère de la Culture",
        "attribution:website": "https://www.data.gouv.fr/datasets/adresses-des-bibliotheques-publiques-2",
    }

    async def start(self):
        yield Request(DATASET_URL)

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json():
            # The dataset also lists administrative offices, mobile libraries
            # and closed reserves which are not public library buildings.
            if location["type_adresse"] != "Bâtiment ouvert":
                continue
            # Avoid closed libraries
            name = location["nom_de_l_etablissement"]
            if "fermé" in name.lower() or "fermee" in name.lower():
                continue

            item = Feature(ref=location["code_bib"], name=name, city=location["ville"], postcode=location["cp"])
            if location["adresse"]:
                item["street_address"] = location["adresse"]
            if location["latitude"]:
                item["lat"] = location["latitude"]
                item["lon"] = location["longitude"]
            if location["telephone"]:
                item["phone"] = location["telephone"]
            # Avoid non-website urls
            if website := location["site_internet"]:
                if not website.lower().startswith(("http://", "https://")):
                    website = f"https://{website}"
                if WEBSITE_REGEX.fullmatch(website):
                    item["website"] = website

            apply_category(Categories.LIBRARY, item)
            apply_yes_no(Extras.WIFI, item, location["connexion_wi_fi"] == "Oui")
            yield item
