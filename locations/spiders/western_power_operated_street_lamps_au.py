import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class WesternPowerOperatedStreetLampsAUSpider(ArcGISFeatureServerSpider):
    """
    The source feature layer contains an enormous amount of duplicate features
    for which the ArcGIS Feature Server query API doesn't allow deduplication
    of. There are over 4 million features returned for this feature layer but
    only approximately 8000 non-duplicated features. The API has a "Return
    Distinct Values" feature but this only works for a single property field
    and including geometry or other fields in the expected output will result
    in this distinct values feature not working and 4 million plus features
    being returned. At 2000 features per request, this spider therefore has to
    make over 2000 requests for just 8000 non-duplicated features to be
    returned.
    """
    name = "western_power_operated_street_lamps_au"
    item_attributes = {"operator": "Western Power", "operator_wikidata": "Q7988180"}
    host = "services2.arcgis.com"
    context_path = "tBLxde4cxSlNUxsM/ArcGIS"
    service_id = "Streetlight_LGA"
    layer_id = "0"
    councils_map = {
        "CITY OF ALBANY": ("City of Albany Council", "Q132397580"),
        "CITY OF ARMADALE": ("Armadale City Council", "Q56477884"),
        "CITY OF BAYWATER": ("Bayswater City Council", "Q56477856"),
        "CITY OF BAYSWATER": ("Bayswater City Council", "Q56477856"),
        "CITY OF BELMONT": ("Belmont City Council", "Q56477892"),
        "CITY OF BUNBURY": ("City of Bunbury Council", "Q106692144"),
        "CITY OF CANINNG": ("Canning City Council", "Q56477868"),
        "CITY OF CANNING": ("Canning City Council", "Q56477868"),
        "CITY OF COCBURN": ("Cockburn City Council", "Q56477844"),
        "CITY OF COCKBURN": ("Cockburn City Council", "Q56477844"),
        "CITY OF FREMANTLE": ("Fremantle City Council", "Q56477934"),
        "CITY OF GOSNELLS": ("Gosnells City Council", "Q56477880"),
        "CITY OF GREATER GERALDTON": ("City of Greater Geraldton Council", "Q132397764"),
        "CITY OF JOODALUP": ("Joondalup City Council", "Q56477908"),
        "CITY OF JOONDALUP": ("Joondalup City Council", "Q56477908"),
        "CITY OF KALAMUNDA": ("Kalamunda City Council", "Q56477947"),
        "CITY OF KALGOORLIE": ("City of Kalgoorlie–Boulder Council", "Q132397828"),
        "CITY OF KALGOORLIE-BOULDER": ("City of Kalgoorlie–Boulder Council", "Q132397828"),
        "CITY OF KWINANA": ("Kwinana City Council", "Q56477942"),
        "CITY OF MADURAH": ("City of Mandurah", "Q1664472"),
        "CITY OF MANDURAH": ("City of Mandurah", "Q1664472"),
        "CITY OF MELVILLE": ("Melville City Council", "Q56477848"),
        "CITY OF NEDLANDS": ("Nedlands City Council", "Q56477828"),
        "CITY OF PERTH": ("Perth City Council", "Q56477938"),
        "CITY OF ROCKHINGHAM": ("Rockingham City Council", "Q56477832"),
        "CITY OF ROCKINGHAM": ("Rockingham City Council", "Q56477832"),
        "CITY OF SITRLING": ("Stirling City Council", "Q56477888"),
        "CITY OF SOUTH PERTH": ("South Perth City Council", "Q56477872"),
        "CITY OF STIRLING": ("Stirling City Council", "Q56477888"),
        "CITY OF SUBIACO": ("Subiaco City Council", "Q56477912"),
        "CITY OF SWAN": ("Swan City Council", "Q56477852"),
        "CITY OF VICTORIA PARK": ("Town of Victoria Park Council", "Q56477864"),
        "CITY OF VINCENT": ("Vincent City Council", "Q56477840"),
        "CITY OF WANNEROO": ("Wanneroo City Council", "Q56477836"),
        "CITY OG STIRLING": ("Stirling City Council", "Q56477888"),
        "CITY STIRLING": ("Stirling City Council", "Q56477888"),
        "SHIRE OF BOYUP BROOK": ("Shire of Boyup Brook Council", "Q132398050"),
        "SHIRE OF BUSSELTON": ("Busselton City Council", "Q132398056"),
        "SHIRE OF CAPEL": ("Shire of Capel Council", "Q132398068"),
        "SHIRE OF COLLIE": ("Shire of Collie Council", "Q132398077"),
        "SHIRE OF COOLGARDIE": ("Shire of Coolgardie Council", "Q132398083"),
        "SHIRE OF DANDARAGAN": ("Shire of Dandaragan Council", "Q132398088"),
        "SHIRE OF DARDANUP": ("Shire of Dardanup Council", "Q132398092"),
        "SHIRE OF DOWERIN": ("Dowerin Shire Council", "Q132398102"),
        "SHIRE OF HARVEY": ("Shire of Harvey Council", "Q132398113"),
        "SHIRE OF IRWIN": ("Shire of Irwin Council", "Q132398140"),
        "SHIRE OF KALAMUNDA": ("Kalamunda City Council", "Q56477947"),
        "SHIRE OF MANJIMUP": ("Shire of Manjimup Council", "Q132398158"),
        "SHIRE OF MUNDARING": ("Shire of Mundaring Council", "Q56477876"),
        "SHIRE OF NAREMBEEN": ("Shire of Narembeen Council", "Q132398179"),
        "SHIRE OF NORTHAM": ("Shire of Northam Council", "Q132398194"),
        "SHIRE OF NORTHAMPTON": ("Shire of Northampton Council", "Q132398213"),
        "SHIRE OF PEPPERMINT GROVE": ("Shire of Peppermint Grove Council", "Q56477916"),
        "SHIRE OF SERPENTINE-JARRAHDALE": ("Shire of Serpentine-Jarrahdale Council", "Q56477860"),
        "TOWN OF BASSENDEAN": ("Town of Bassendean Council", "Q56477930"),
        "TOWN OF CAMBRIDGE": ("Town of Cambridge Council", "Q56477904"),
        "TOWN OF CLAREMONT": ("Town of Claremont Council", "Q56477896"),
        "TOWN OF COTTESLOE": ("Town of Cottesloe Council", "Q56477926"),
        "TOWN OF KWINANA": ("Kwinana City Council", "Q56477942"),
        "TOWN OF MOSMAN PARK": ("Town of Mosman Park Council", "Q56477920"),
        "TOWN OF MOSMON PARK": ("Town of Mosman Park Council", "Q56477920"),
        "TOWN OF VICTORIA PARK": ("Town of Victoria Park Council", "Q56477864"),
        "TOWN OF VINCENT": ("Vincent City Council", "Q56477840"),
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["PICK_ID"]
        item["state"] = "WA"
        apply_category(Categories.STREET_LAMP, item)
        if owner_name := feature.get("OWNER"):
            owner_name = re.sub(r"\s+", " ", owner_name).strip()
            if owner_name in self.councils_map.keys(): 
                item["extras"]["owner"] = self.councils_map[owner_name][0]
                item["extras"]["owner:wikidata"] = self.councils_map[owner_name][1]
            else:
                item["extras"]["owner"] = owner_name
                self.logger.warning("Unknown street lamp owner: {}".format(owner_name))
        yield item
