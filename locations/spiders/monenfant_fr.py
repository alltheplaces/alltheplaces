# TODO: find specific tags for the still-generic types: MAM (4447), LINF (2596),
# SMF (333), ER (249), LRES (173).
# ALSH is excluded from STRUCTURE_TYPES: the France-wide request
# times out > 600 s server-side.

import re
from typing import Iterable

from pyproj import Transformer
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MonenfantFRSpider(JSONBlobSpider):
    name = "monenfant_fr"
    allowed_domains = ["monenfant.fr"]

    # Types of the monenfant.fr search form (checkbox "id"/"for"), one WMS
    # request each ("types" viewparam takes a single value). Excluded:
    # ASM and GADM (individual persons / home childcare, not places),
    # ALSH times out > 600 s for France-wide request, so excluded for now.
    STRUCTURE_TYPES = ["RPE", "LINF", "EAJE", "MAM", "LRES", "LAEP", "SMF", "ER"]

    # WMS GetFeatureInfo on search_full: the only GeoServer layer with
    # tel/mail/address (the WFS layers do not expose them). The EPSG:3857 bbox
    # is mainland France + Corsica.
    # FEATURE_COUNT is above the largest observed per-type total; extract_json
    # raises if it is ever reached (GetFeatureInfo truncates silently otherwise).
    FEATURE_COUNT = 25000
    WMS_URL = (
        "https://monenfant.fr/geoserver/MonEnfant/wms"
        "?bbox=-612257.2,5012341.7,1090931.0,6710219.1"
        "&srs=EPSG:3857&crs=EPSG:3857"
        "&format=application/json&info_format=application/json"
        "&request=GetFeatureInfo&service=WMS"
        "&layers=MonEnfant:search_full&query_layers=MonEnfant:search_full"
        "&version=1.1.1"
        f"&feature_count={FEATURE_COUNT}"
        "&width=1216&height=328&x=608&y=164"
        "&viewparams=types:{structure_type};x:2.5;y:46.6"
        "&buffer=800"
    )
    start_urls = []
    for _t in STRUCTURE_TYPES:  # loop: a comprehension cannot see class-body names
        start_urls.append(WMS_URL.format(structure_type=_t))

    locations_key = "features"
    custom_settings = {"DOWNLOAD_TIMEOUT": 600}  # France-wide responses are huge

    # French OSM consensus (https://wiki.openstreetmap.org/wiki/FR:Tag:amenity%3Dchildcare):
    # childcare structures are amenity=kindergarten, not amenity=childcare.
    # Parental-support / family-mediation services stay amenity=social_facility.
    CATEGORY_BY_TYPE = {
        "EAJE": Categories.KINDERGARTEN,  # crèche
        "MAM": Categories.KINDERGARTEN,  # maison d'assistantes maternelles
        "RPE": Categories.SOCIAL_FACILITY,  # relais petite enfance
        "LINF": Categories.SOCIAL_FACILITY,  # lieu d'information
        "LRES": Categories.SOCIAL_FACILITY,  # espace de ressources pour les familles
        "LAEP": Categories.SOCIAL_FACILITY,  # lieu d'accueil enfants-parents
        "SMF": Categories.SOCIAL_FACILITY,  # service de médiation familiale
        "ER": Categories.SOCIAL_FACILITY,  # espace de rencontre
        "ALSH": Categories.COMMUNITY_CENTRE,  # accueil de loisirs (> 3 ans)
    }

    # kindergarten:FR sub-tags, best-effort from the establishment name, most specific first
    KINDERGARTEN_FR_PATTERNS = [
        (r"halte[\s-]*garderie", "halte_garderie"),
        (r"jardin[\s-]*d['’]?\s?enfants", "jardin_enfants"),
        (r"micro[\s-]*cr[eè]che", "microcrèche"),
        (r"multi[\s-]*accueil", "multiaccueil"),
        (r"parentale", "crèche_parentale"),
        (r"familiale", "crèche_familiale"),
        (r"collective", "crèche_collective"),
    ]

    def extract_json(self, response: TextResponse) -> list[dict]:
        data = response.json()
        if data["numberReturned"] >= self.FEATURE_COUNT:
            raise RuntimeError(f"feature_count {self.FEATURE_COUNT} reached: results may be truncated")
        return data[self.locations_key]

    def pre_process_data(self, feature: dict) -> None:
        props = feature["properties"]
        feature.update(props)
        if props.get("mail"):
            feature["email"] = props["mail"]
        if props.get("siteweb"):
            feature["website"] = props["siteweb"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature.get("firstname"):  # individual person, not a place
            return
        apply_category(self.CATEGORY_BY_TYPE.get(feature.get("type"), Categories.SOCIAL_FACILITY), item)
        # RPE (relais petite enfance / relais d'assistantes maternelles): parents support, not childcare
        # Ref: https://forum.openstreetmap.fr/t/comment-cartographier-un-relai-dassistante-maternel-ram-relais-petite-enfance-rpe/32193/6
        if feature.get("type") == "RPE":
            item["extras"]["social_facility"] = "outreach"
            item["extras"]["social_facility:for"] = "parents"
        # ALSH (accueil de loisirs sans hébergement, > 3 ans): youth centre, not childcare
        # Ref: https://forum.openstreetmap.fr/t/comment-cartographier-un-relai-dassistante-maternel-ram-relais-petite-enfance-rpe/32193/7
        if feature.get("type") == "ALSH":
            item["extras"]["community_centre:for"] = "child"
            item["extras"]["community_centre"] = "youth_centre"
        # LAEP (lieu d'accueil enfants-parents): drop-in child/parent space, no formal education
        # Ref: https://lists.openstreetmap.org/pipermail/talk-fr/2018-October/090713.html
        if feature.get("type") == "LAEP" or "LAEP" in (item.get("name") or "").upper():
            item["extras"]["social_facility"] = "outreach"
            item["extras"]["social_facility:for"] = "child;parent"
            item["extras"]["min_age"] = "*"
            item["extras"]["max_age"] = "6"
            item["extras"]["supervised"] = "yes"
        if feature.get("type") == "EAJE" and item.get("name"):
            for pattern, subtag in self.KINDERGARTEN_FR_PATTERNS:
                if re.search(pattern, item["name"], re.IGNORECASE):
                    item["extras"]["kindergarten:FR"] = subtag
                    break
        # source coords are EPSG:3857; from_crs(3857, 4326) returns (lat, lon) (axis order)
        item["lat"], item["lon"] = Transformer.from_crs(3857, 4326).transform(*feature["geometry"]["coordinates"])
        item.pop("geometry", None)
        if addr := item.get("addr_full"):  # "17 rue du Moulin 67202 WOLFISHEIM"
            if match := re.match(r"^(.*) (\d{5}) (.+)$", addr):
                item["street_address"], item["postcode"], item["city"] = match.groups()
                del item["addr_full"]
        yield item
