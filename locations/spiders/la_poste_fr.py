from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses

# https://www.data.gouv.fr/datasets/liste-des-bureaux-de-poste-agences-postales-et-relais-poste
DATASET_URL = "https://data.laposte.fr/data-fair/api/v1/datasets/laposte-poincont2/lines"
PAGE_SIZE = 10000

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

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url=f"{DATASET_URL}?size={PAGE_SIZE}")

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
