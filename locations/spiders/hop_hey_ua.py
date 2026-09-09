import re
from ast import literal_eval

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_RU, OpeningHours
from locations.items import Feature

MARKERS_PATTERN = re.compile(r"markers:\s*(\[.*?\]),\s*options:", re.S)

# The site has no single "all stores" listing; each city code returns markers
# for that city plus nearby towns, so results overlap and must be deduplicated.
CITY_CODES = [
    "kyiv",
    "belogorodka",
    "boryspol",
    "boyarka",
    "brovari",
    "bucha",
    "vorzel",
    "vishnevoe",
    "vyshgorod",
    "gatnoe",
    "gora",
    "gorenka",
    "gostomel",
    "gnedin",
    "zazimye",
    "irpen",
    "kalinovka",
    "knyazhichi",
    "kotsyubinskoe",
    "kryukovshchina",
    "lesniki",
    "nemeshaevo",
    "novoselki",
    "pogreby",
    "puhovka",
    "svyatopetrovskoe",
    "schastlivoe",
    "tarasovka",
    "hodosovka",
    "hotov",
    "chabany",
    "chajki",
    "yurovka",
    "belayatserkov",
    "terezino",
    "tomilovka",
    "trushki",
    "fursy",
    "shkarovka",
    "dnepr",
    "dndz",
    "elizavetovka",
    "karnauhovka",
    "kuleshi",
    "nikolaevka",
    "shulgovka",
    "krv",
    "avangard",
    "volnoe",
    "lozovatka",
    "maryanovka",
    "novopole",
    "nsk",
    "novoselovka",
    "orlovshhina",
    "peschanka",
    "obuhovka",
    "pavlograd",
    "podgorodnoe",
    "sinelnikovo",
    "ternovka",
    "zaporozhe",
    "baburka",
    "balabino",
    "kushugum",
    "matveevka",
    "solnechnoe",
    "poltava",
    "gorbanevka",
    "rossoshency",
    "stasi",
    "kremenchuk",
    "vlasovka",
    "krivushi",
    "malamovka",
    "svetlovodsk",
    "sosnovka",
    "chechelevo",
    "dmitrovka",
    "keleberda",
    "kirovograd",
    "berezhinka",
    "katerinovka",
    "klincy",
    "oboznovka",
    "sozonovka",
    "sokolovskoe",
    "subbotcy",
    "fedorovka",
    "chernyahovka",
    "nikolaev",
    "od",
    "kotovka",
    "korsuntsy",
    "krasnoselka",
    "leski",
    "fontanka",
    "svetloe",
    "tairovo",
    "chernomorsk",
    "aleksandrovka",
    "yuzhnyy",
    "sychavka",
    "koshary",
    "cherkassy",
]


class HopHeyUASpider(Spider):
    name = "hop_hey_ua"
    item_attributes = {"brand": "Hop Hey", "brand_wikidata": "Q104829481"}
    allowed_domains = ["hophey.ua"]
    start_urls = [f"https://hophey.ua/ru/shops/?CITY_CODE={code}" for code in CITY_CODES]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_refs = set()

    def parse(self, response: Response):
        if not (match := MARKERS_PATTERN.search(response.text)):
            return

        for marker in literal_eval(match.group(1)):
            ref = marker["ID"]
            if ref in self.seen_refs:
                continue
            self.seen_refs.add(ref)

            item = Feature()
            item["ref"] = ref
            item["lat"] = marker.get("GPS_N")
            item["lon"] = marker.get("GPS_S")
            item["addr_full"] = marker.get("ADDRESS_CLEARED")
            item["country"] = "UA"

            oh = OpeningHours()
            for schedule in marker.get("SCHEDULE_SPLITTED", []):
                oh.add_ranges_from_string(schedule, days=DAYS_RU)
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_ALCOHOL, item)

            yield item
