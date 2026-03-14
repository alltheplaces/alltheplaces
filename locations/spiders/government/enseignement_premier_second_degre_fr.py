from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider

# https://www.data.gouv.fr/datasets/adresse-et-geolocalisation-des-etablissements-denseignement-des-premier-et-second-degres

NATURE_UAI_CATEGORY_MAP = {
    # Primary education (nature_uai 100-199)
    101: ("kindergarten", Categories.KINDERGARTEN),  # ECOLE MATERNELLE
    103: ("kindergarten", Categories.KINDERGARTEN),  # ECOLE MATERNELLE D APPLICATION
    151: ("primary", Categories.SCHOOL),  # ECOLE DE NIVEAU ELEMENTAIRE
    153: ("primary", Categories.SCHOOL),  # ECOLE ELEMENTAIRE D APPLICATION
    160: ("primary", Categories.SCHOOL),  # ECOLE DE PLEIN AIR
    162: ("primary;special_education_needs", Categories.SCHOOL),  # ECOLE DE NIVEAU ELEMENTAIRE SPECIALISEE
    169: ("primary", Categories.SCHOOL),  # ECOLE REGIONALE DU PREMIER DEGRE
    170: ("primary", Categories.SCHOOL),  # ECOLE SANS EFFECTIFS PERMANENTS
    # Secondary education (nature_uai 300-399)
    300: ("secondary", Categories.SCHOOL),  # LYCEE ENSEIGNT GENERAL ET TECHNOLOGIQUE
    301: ("secondary", Categories.SCHOOL),  # LYCEE D ENSEIGNEMENT TECHNOLOGIQUE
    302: ("secondary", Categories.SCHOOL),  # LYCEE D ENSEIGNEMENT GENERAL
    306: ("secondary", Categories.SCHOOL),  # LYCEE POLYVALENT
    307: ("secondary", Categories.SCHOOL),  # LYCEE ENS GENERAL TECHNO PROF AGRICOLE
    310: ("secondary", Categories.SCHOOL),  # LYCEE CLIMATIQUE
    312: ("secondary;special_education_needs", Categories.SCHOOL),  # ECOLE SECONDAIRE SPECIALISEE
    315: ("secondary", Categories.SCHOOL),  # LYCEE EXPERIMENTAL
    320: ("secondary", Categories.SCHOOL),  # LYCEE PROFESSIONNEL
    332: ("secondary", Categories.SCHOOL),  # ECOLE PROFESSIONNELLE SPECIALISEE
    334: ("secondary", Categories.SCHOOL),  # SECTION D ENSEIGNEMENT PROFESSIONNEL
    335: ("secondary", Categories.SCHOOL),  # SECTION ENSEIGT GENERAL ET TECHNOLOGIQUE
    340: ("secondary", Categories.SCHOOL),  # COLLEGE
    342: ("secondary", Categories.SCHOOL),  # GROUPEMENT D OBSERVATION DISPERSE
    344: ("secondary", Categories.SCHOOL),  # CETAD (TOM)
    345: ("secondary", Categories.SCHOOL),  # CENTRE DE JEUNES ADOLESCENTS
    346: ("secondary", Categories.SCHOOL),  # COLLEGE EXPERIMENTAL
    349: ("secondary", Categories.SCHOOL),  # ETABLISSEMENT DE REINSERTION SCOLAIRE
    350: ("secondary", Categories.SCHOOL),  # COLLEGE CLIMATIQUE
    352: ("secondary;special_education_needs", Categories.SCHOOL),  # COLLEGE SPECIALISE
    370: ("secondary", Categories.SCHOOL),  # ETAB REGIONAL/LYCEE ENSEIGNEMENT ADAPTE
    380: ("secondary", Categories.SCHOOL),  # MAISON FAMILIALE RURALE EDUCATION ORIENT
    390: ("secondary", Categories.SCHOOL),  # SECTION ENSEIGNT GEN. ET PROF. ADAPTE
}


class EnseignementPremierSecondDegreFRSpider(OpendatasoftExploreSpider):
    name = "enseignement_premier_second_degre_fr"
    dataset_attributes = OpendatasoftExploreSpider.dataset_attributes | {
        "license": "Licence Ouverte / Open Licence version 2.0",
        "license:website": "https://www.etalab.gouv.fr/licence-ouverte-open-licence/",
        "license:wikidata": "Q29949417",
        "attribution": "required",
        "attribution:name": "Ministere de l'Education Nationale - data.education.gouv.fr",
    }
    api_endpoint = "https://data.education.gouv.fr/api/explore/v2.1/"
    dataset_id = "fr-en-adresse-et-geolocalisation-etablissements-premier-et-second-degre"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature.get("etat_etablissement") != 1:
            self.crawler.stats.inc_value("atp/items/skipped")
            return

        item["ref"] = feature.get("numero_uai")
        item["name"] = feature.get("appellation_officielle")
        item["branch"] = feature.get("patronyme_uai")
        item["street_address"] = feature.get("adresse_uai")
        item["postcode"] = feature.get("code_postal_uai")
        item["city"] = feature.get("libelle_commune")
        item["state"] = feature.get("libelle_region")
        item["extras"]["ref:FR:UAI"] = feature.get("numero_uai")

        if feature.get("secteur_public_prive_libe") == "Public":
            item["extras"]["operator:type"] = "government"
        elif feature.get("secteur_public_prive_libe") == "Privé":
            item["extras"]["operator:type"] = "private"

        nature_uai = feature.get("nature_uai")
        if mapping := NATURE_UAI_CATEGORY_MAP.get(nature_uai):
            school_type, category = mapping
            item["extras"]["school"] = school_type
            apply_category(category, item)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_nature_uai/{nature_uai}")
            apply_category(Categories.SCHOOL, item)

        yield item
