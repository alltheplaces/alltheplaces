import re

from scrapy.http import Response
from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, add_list, apply_category
from locations.items import Feature
from locations.licenses import Licenses

# https://www.data.gouv.fr/datasets/musees-de-france-base-museofile
DATASET_URL = "https://www.data.gouv.fr/api/1/datasets/r/5ccd6238-4fb0-4b2c-b14a-581909489320"
WEBSITE_REGEX = re.compile(r"https?://(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}(?:/\S*)?$", re.IGNORECASE)
# Domaine_thematique values (lowercased) -> OSM museum=* value
DOMAIN_MUSEUM_TYPES = {
    domain: museum_type
    for museum_type, domains in {
        "history": [
            "histoire",
            "mémoire de l'esclavage",
            "musée de société",
            "esclavage, société de plantation, histoire de la réunion, colonisation, industrie sucrière",
        ],
        "archaeological": ["archéologie", "archéologie du bâti", "gallo-romain", "protohistoire", "égyptien", "grec"],
        "military": ["militaria"],
        "ethnography": ["ethnologie", "afrique", "asie", "océanie", "amérique", "amériques", "inde"],
        "art": [
            "beaux-arts",
            "arts décoratifs",
            "art moderne et contemporain",
            "photographie",
            "peinture",
            "arts de l'islam",
            "design",
            "mode et textile",
            "mode",
            "textile",
            "couturier",
            "arts graphiques",
            "céramique",
            "sculpture",
            "imprimé",
            "musique - chant - danse",
            "musique",
            "numismatique",
            "littérature",
        ],
        "nature": ["sciences de la nature", "sciences naturelles"],
        "science": ["sciences fondamentales", "sciences"],
        "technology": ["technique et industrie", "techniques et industrie", "sciences et techniques", "techniques"],
    }.items()
    for domain in domains
}


# No brand/brand_wikidata: the dataset covers independent museums, not a single chain.
class MuseesDeFranceFRSpider(CSVFeedSpider):
    name = "musees_de_france_fr"
    allowed_domains = ["data.gouv.fr"]
    start_urls = [DATASET_URL]
    delimiter = "|"
    # data.gouv.fr publishes this stable resource URL as the dataset's file,
    # but its robots.txt blocks automated access to the /api/1/datasets/r/ path.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    dataset_attributes = Licenses.ETALAB2.value | {
        "source": "api",
        "attribution:name": "Ministère de la Culture",
        "attribution:website": "https://www.data.gouv.fr/datasets/musees-de-france-base-museofile",
    }

    def parse_row(self, response: Response, row: dict[str, str]) -> Feature:
        item = Feature(ref=row["Identifiant"], name=row["Nom_officiel"], postcode=row["Code_postal"], city=row["Ville"])
        if row["Adresse"]:
            item["street_address"] = row["Adresse"]
        if row["Coordonnees"]:
            item["lat"], item["lon"] = row["Coordonnees"].split(",")
        if row["Telephone"]:
            item["phone"] = row["Telephone"]
        website = row["URL"].strip().lstrip("/")
        if website and not website.lower().startswith(("http://", "https://")):
            website = f"https://{website}"
        if website and WEBSITE_REGEX.fullmatch(website):  # avoid non-website urls
            item["website"] = website

        apply_category(Categories.MUSEUM, item)
        for domain in row["Domaine_thematique"].split(";"):
            museum_type = DOMAIN_MUSEUM_TYPES.get(" ".join(domain.lower().split()))
            if museum_type:
                add_list("museum", museum_type, item)
        return item
