import csv
from typing import Iterable

from pyproj import Transformer
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses

# categagretab (aggregate category) to OSM category.
AGGREGATE_CATEGORIES = {
    "1101": Categories.HOSPITAL,  # Centres Hospitaliers Régionaux
    "1102": Categories.HOSPITAL,  # Centres Hospitaliers
    "1103": Categories.HOSPITAL,  # Centres Hospitaliers Spécialisés Lutte Maladies Mentales
    "1104": Categories.HOSPITAL,  # Centres de Lutte contre le Cancer
    "1106": Categories.HOSPITAL,  # Hôpitaux Locaux
    "1107": Categories.HOSPITAL,  # Etablissements de santé privé autorisés en SSR
    "1109": Categories.HOSPITAL,  # Etablissements de Soins de Longue Durée
    "1110": Categories.HOSPITAL,  # Etablissements de Soins de Courte Durée
    "1111": Categories.CLINIC,  # Autres Etablissements de Lutte contre les Maladies Mentales
    "1203": Categories.DIALYSIS,  # Dialyse Ambulatoire
    "2201": Categories.CLINIC,  # Dispensaires ou Centres de Soins
    "2202": Categories.CLINIC,  # Etablissements de PMI et de Planification Familiale
    "2205": Categories.HOSPITAL,  # Etab.de soins relevant du service de santé des armées
    "2206": Categories.CLINIC,  # Centres de Santé
    "3101": Categories.MEDICAL_LABORATORY,  # Laboratoires de Biologie Médicale
    "3401": Categories.BLOOD_DONATION,  # Transfusion Sanguine
    "3406": Categories.BIRTHING_CENTRE,  # Maison de Naissance
    "4101": Categories.SOCIAL_FACILITY,  # Etab.Educ.Spéciale pour Déficients Mentaux et Handicapés
    "4102": Categories.SOCIAL_FACILITY,  # Etab.Educ Spéciale pour Enfants Trouble Conduite et Comport
    "4103": Categories.SOCIAL_FACILITY,  # Etablissements d'Education Spéciale pour Handicapés Moteurs
    "4104": Categories.SOCIAL_FACILITY,  # Etab.Education Spéciale pour Déficients Sensoriels
    "4105": Categories.SOCIAL_FACILITY,  # Etablissements et Services Hébergement Enfants Handicapés
    "4106": Categories.SOCIAL_FACILITY_OUTREACH,  # Services à Domicile ou Ambulatoires pour Handicapés
    "4301": Categories.SOCIAL_FACILITY,  # Etab. et Services d'Hébergement pour Adultes Handicapés
    "4305": Categories.SOCIAL_FACILITY_OUTREACH,  # Services de Maintien à Domicile pour Handicapés
    "4401": Categories.NURSING_HOME,  # Etablissements d'Hébergement pour Personnes Âgées
    "4402": Categories.SOCIAL_FACILITY,  # Services de Maintien à Domicile pour Personnes Âgées
    "4403": Categories.SOCIAL_FACILITY_OUTREACH,  # Services Sociaux en Faveur des Personnes Âgées
    "4501": Categories.SOCIAL_FACILITY,  # Etablissements de l'Aide Sociale à l'Enfance
    "4502": Categories.SOCIAL_FACILITY,  # Etab.et Services du Ministère de la Justice pour Mineurs
    "4504": Categories.SOCIAL_FACILITY_OUTREACH,  # Services Concourant à la Protection de l'Enfance
    "4601": Categories.SOCIAL_FACILITY,  # Etablissements pour Adultes et Familles en Difficulté
    "4602": Categories.SOCIAL_FACILITY,  # Autres Etablissements Sociaux d'Hébergement et d'Accueil
    "4604": Categories.SOCIAL_FACILITY,  # Autres Etablissements médico-sociaux
    "4605": Categories.SOCIAL_FACILITY_OUTREACH,  # Etablissements et services multi-clientèles
    "4607": Categories.SOCIAL_FACILITY,  # Logements en Structure Collective
    "4608": Categories.SOCIAL_FACILITY_OUTREACH,  # Protection des majeurs
    "6101": Categories.COLLEGE,  # Etablissements de Formation des Personnels Sanitaires
    "6201": Categories.COLLEGE,  # Etablissements de Formation des Personnels Sociaux
    "6301": Categories.COLLEGE,  # Etablissements de Formation Polyvalente
}

# categetab (detailed category) where it is more specific than its aggregate.
CATEGORIES = {
    "202": Categories.ASSISTED_LIVING,  # Résidences autonomie
    "462": Categories.SOCIAL_FACILITY,  # Lieux de Vie et d'Accueil
    "603": Categories.CLINIC,  # Maison de santé (L.6223-3)
    "617": Categories.CLINIC_URGENT,  # Lieux de soins non programmés
    "620": Categories.PHARMACY,  # Pharmacie d'Officine
    "627": Categories.PHARMACY,  # Propharmacie
    "628": Categories.PHARMACY,  # Pharmacie Minière
    "629": Categories.PHARMACY,  # Pharmacie Mutualiste
    "641": Categories.PHARMACY,  # Antenne de Pharmacie d'officine
}

# Coordinate systems named without an EPSG code in sourcecoordet.
UTM_ZONES = {
    "WGS84/UTM zone 21N (St-Pierre-et-Miquelon)": 32621,
    "WGS84/UTM zone 1S (Wallis-et-Futuna)": 32701,
}


class GovFinessFRSpider(Spider):
    name = "gov_finess_fr"
    allowed_domains = ["www.data.gouv.fr", "static.data.gouv.fr"]
    # https://www.data.gouv.fr/datasets/finess-extraction-du-fichier-des-etablissements
    start_urls = ["https://www.data.gouv.fr/api/1/datasets/r/98f3161f-79ff-4f16-8f6a-6d571a80fea2"]
    # robots.txt disallows /api/, which is where data.gouv.fr's stable download links point.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    dataset_attributes = Licenses.ETALAB2.value | {
        "attribution:name": "FINESS, Ministère de la Santé",
        "attribution:website": "https://finess.sante.gouv.fr/",
    }

    def parse(self, response: Response) -> Iterable[Feature]:
        establishments = {}
        transformers = {}
        for row in csv.reader(response.body.decode("utf-8").splitlines(), delimiter=";"):
            if row[0] == "structureet":
                establishments[row[1]] = row
                continue
            if row[0] != "geolocalisation":
                continue
            establishment = establishments.pop(row[1])
            item = Feature()
            item["ref"] = item["extras"]["ref:FR:FINESS"] = establishment[1]
            item["name"] = establishment[4] or establishment[3]
            item["housenumber"] = establishment[7] + establishment[10]
            item["street"] = " ".join(filter(None, [establishment[8], establishment[9]]))
            item["postcode"], item["city"] = establishment[15].split(" ", 1)
            item["phone"] = establishment[16]
            item["extras"]["ref:FR:SIRET"] = establishment[22]
            if category := CATEGORIES.get(establishment[18]) or AGGREGATE_CATEGORIES.get(establishment[20]):
                apply_category(category, item)

            # Precision 4 is the centroid of the commune.
            source = row[4].split(",")
            if row[2] and source[0] != "4":
                crs = UTM_ZONES.get(source[-1]) or source[-1].split(" ")[0]
                if crs not in transformers:
                    transformers[crs] = Transformer.from_crs(crs, "EPSG:4326")
                item["lat"], item["lon"] = transformers[crs].transform(float(row[2]), float(row[3]))
            yield item
