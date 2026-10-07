from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider

# https://www.data.gouv.fr/datasets/adresse-et-geolocalisation-des-etablissements-denseignement-des-premier-et-second-degres

# nature_uai: (school, isced:level, category)
# ISCED 2011: 0 = école maternelle, 1 = école élémentaire, 2 = collège (6e-3e), 3 = lycée (2nde-Tle, CAP/bac pro).
# Codes with isced:level None span levels or are not yet verified against the Ministry nomenclature.
NATURE_UAI_CATEGORY_MAP = {
    # Primary education (nature_uai 100-199)
    101: ("kindergarten", "0", Categories.KINDERGARTEN),  # ECOLE MATERNELLE
    103: ("kindergarten", "0", Categories.KINDERGARTEN),  # ECOLE MATERNELLE D APPLICATION
    151: ("primary", "1", Categories.SCHOOL),  # ECOLE DE NIVEAU ELEMENTAIRE
    153: ("primary", "1", Categories.SCHOOL),  # ECOLE ELEMENTAIRE D APPLICATION
    160: ("primary", "1", Categories.SCHOOL),  # ECOLE DE PLEIN AIR
    162: ("primary;special_education_needs", "1", Categories.SCHOOL),  # ECOLE DE NIVEAU ELEMENTAIRE SPECIALISEE
    169: ("primary", "1", Categories.SCHOOL),  # ECOLE REGIONALE DU PREMIER DEGRE
    170: ("primary", "1", Categories.SCHOOL),  # ECOLE SANS EFFECTIFS PERMANENTS
    # Lower secondary: collèges (ISCED 2)
    340: ("secondary", "2", Categories.SCHOOL),  # COLLEGE
    346: ("secondary", "2", Categories.SCHOOL),  # COLLEGE EXPERIMENTAL
    350: ("secondary", "2", Categories.SCHOOL),  # COLLEGE CLIMATIQUE
    352: ("secondary;special_education_needs", "2", Categories.SCHOOL),  # COLLEGE SPECIALISE
    390: ("secondary", "2", Categories.SCHOOL),  # SECTION ENSEIGNT GEN. ET PROF. ADAPTE (SEGPA, in a collège)
    # Upper secondary: lycées (ISCED 3)
    300: ("secondary", "3", Categories.SCHOOL),  # LYCEE ENSEIGNT GENERAL ET TECHNOLOGIQUE
    301: ("secondary", "3", Categories.SCHOOL),  # LYCEE D ENSEIGNEMENT TECHNOLOGIQUE
    302: ("secondary", "3", Categories.SCHOOL),  # LYCEE D ENSEIGNEMENT GENERAL
    306: ("secondary", "3", Categories.SCHOOL),  # LYCEE POLYVALENT
    307: ("secondary", "3", Categories.SCHOOL),  # LYCEE ENS GENERAL TECHNO PROF AGRICOLE
    310: ("secondary", "3", Categories.SCHOOL),  # LYCEE CLIMATIQUE
    312: ("secondary;special_education_needs", "3", Categories.SCHOOL),  # ECOLE SECONDAIRE SPECIALISEE (2 D CYCLE)
    315: ("secondary", "3", Categories.SCHOOL),  # LYCEE EXPERIMENTAL
    320: ("secondary", "3", Categories.SCHOOL),  # LYCEE PROFESSIONNEL
    334: ("secondary", "3", Categories.SCHOOL),  # SECTION D ENSEIGNEMENT PROFESSIONNEL (SEP, in a lycée)
    335: ("secondary", "3", Categories.SCHOOL),  # SECTION ENSEIGT GENERAL ET TECHNOLOGIQUE (SGT, in a lycée)
    # Other secondary establishments, level not assigned
    332: ("secondary", None, Categories.SCHOOL),  # ECOLE PROFESSIONNELLE SPECIALISEE
    342: ("secondary", None, Categories.SCHOOL),  # GROUPEMENT D OBSERVATION DISPERSE
    344: ("secondary", None, Categories.SCHOOL),  # CETAD (TOM)
    345: ("secondary", None, Categories.SCHOOL),  # CENTRE DE JEUNES ADOLESCENTS
    349: ("secondary", None, Categories.SCHOOL),  # ETABLISSEMENT DE REINSERTION SCOLAIRE
    370: ("secondary", None, Categories.SCHOOL),  # ETAB REGIONAL/LYCEE ENSEIGNEMENT ADAPTE (collège and lycée levels)
    380: ("secondary", None, Categories.SCHOOL),  # MAISON FAMILIALE RURALE EDUCATION ORIENT (collège and lycée levels)
}


class EnseignementPremierSecondDegreFRSpider(OpendatasoftExploreSpider):
    name = "enseignement_premier_second_degre_fr"
    dataset_attributes = (
        OpendatasoftExploreSpider.dataset_attributes
        | Licenses.ETALAB2.value
        | {
            "attribution:name": "Ministère de l’Éducation Nationale",
            "attribution:website": "https://data.education.gouv.fr/",
        }
    )
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
            school_type, isced_level, category = mapping
            item["extras"]["school"] = school_type
            if isced_level:
                item["extras"]["isced:level"] = isced_level
            apply_category(category, item)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_nature_uai/{nature_uai}")
            apply_category(Categories.SCHOOL, item)

        yield item
