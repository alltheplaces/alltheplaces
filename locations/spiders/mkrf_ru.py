from scrapy.http import Request
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours

CATEGORY_MAPPING = {
    "kinoteatry": Categories.CINEMA,
    "muzei-i-galerei": Categories.MUSEUM,
    "biblioteki": Categories.LIBRARY,
    "dvorcy-kultury-i-kluby": Categories.COMMUNITY_CENTRE,
}

MUSEUM_TYPES = {
    "Авиации и космонавтики": "aviation",
    "Автотранспорта": "transport",
    "Антропологический": "archaeological",
    "Археологический": "archaeological",
    "Архитектурно-ансамблевый": "architecture",
    "Архитектурный": "architecture",
    "Биологический": "nature",
    "Ботанический сад, Парк": "nature",
    "Военно-Исторический": "military",
    "Военно-Морской": "military",
    "Геологический": "geology",
    "Горного дела": "geology",
    "Дворцово-парковый ансамбль": "architecture",
    "Дек.прикладного и нар. искусства": "art",
    "Естественнонаучный": "nature",
    "Жел./дор. транспорта и метро": "transport",
    "Зоопарк, Аквариум": "nature",
    "Изобразительного исскуства": "art",
    "Истории организаций": "history",
    "Историко-Революционный": "history",
    "Историко-бытовой": "history",
    "Исторический": "history",
    "Краеведческий": "history",
    "Литературный": "art",
    "Медицинский": "science",
    "Морской": "maritime",
    "Музеи скульптуры": "art",
    "Музей современного искусства": "art",
    "Музей-заповедник": None,
    "Музей-усадьба": "architecture",
    "Музей-храм, монастырь": "architecture",
    "Музыкальный": "art",
    "Науки, техники и отраслей н.х.": "technology",
    "Общеисторический": "history",
    "Отраслевые": "history",
    "Палеонтологический": "paleontology",
    "Персональный, мемориальный": "person",
    "Сельского хозяйства": "agriculture",
    "Спортивная": "sport",
    "Средств связи": "technology",
    "Судостроения": "maritime",
    "Театральный": "art",
    "Фотографии": "art",
    "Художественный": "art",
    "Художественных ремесел": "art",
    "Художественных ремёсел": "art",
    "Этнографический": "ethnography",
}


class MkrfRUSpider(Spider):
    name = "mkrf_ru"
    allowed_domains = ["opendata.mkrf.ru"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True
    dataset_attributes = {
        "attribution": "required",
        "attribution:name:en": "Ministry of Culture of the Russian Federation",
        "attribution:name:ru": "Министерство культуры Российской Федерации",
        "attribution:website": "https://opendata.mkrf.ru/",
        "license:website": "https://opendata.mkrf.ru/item/license",
        "use:commercial": "permit",
    }
    # TODO: add more datasets from https://opendata.mkrf.ru/item/api
    datasets = ["museums", "cinema", "libraries", "culture_palaces_clubs"]

    api_key = "be088ddb94bfd718a196c7ac7f67d32303ba69681948ec0a21744cdd4f78bd16"

    def start_requests(self):
        for dataset in self.datasets:
            yield Request(
                url=f"https://opendata.mkrf.ru/v2/{dataset}/$?l=1000",
                headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
            )

    def parse(self, response):
        if pois := response.json().get("data"):
            if len(pois):
                self.logger.info(f"Found {len(pois)} POIs for {response.url}")
                for poi in pois:
                    yield from self.parse_poi(poi)

                if next_page := response.json().get("nextPage"):
                    yield Request(
                        url=next_page,
                        callback=self.parse,
                        headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
                    )

    def parse_poi(self, poi):
        poi_attributes = poi.get("data", {}).get("general")
        if poi_attributes:
            item = DictParser.parse(poi_attributes)
            item["street"] = None

            # 'locale' is inconsistent, sometimes it's is city, sometimes it's region - skip it
            if address := poi_attributes.get("address"):
                item["street_address"] = address.get("street")
                item["addr_full"] = address.get("fullAddress")
                if coordinates := address.get("mapPosition", {}).get("coordinates"):
                    if len(coordinates) != 0:
                        item["lat"] = coordinates[1]
                        item["lon"] = coordinates[0]

            if contacts := poi_attributes.get("contacts"):
                item["email"] = contacts.get("email")
                item["website"] = contacts.get("website")
                if phones := contacts.get("phones"):
                    item["phone"] = "; ".join([phone["value"] for phone in phones])

            item["image"] = poi_attributes.get("image", {}).get("url")
            self.parse_category(item, poi_attributes)
            self.parse_hours(item, poi_attributes)
            self.parse_museum_types(item, poi_attributes)

            yield item

    def parse_category(self, item, poi_attributes):
        if category := poi_attributes.get("category"):
            if category_tag := CATEGORY_MAPPING.get(category.get("sysName", {})):
                apply_category(category_tag, item)

    def parse_hours(self, item, poi_attributes):
        if working_schedule := poi_attributes.get("workingSchedule"):
            try:
                oh = OpeningHours()
                for k, v in working_schedule.items():
                    oh.add_range(DAYS[int(k)], v.get("from"), v.get("to"), "%H:%M:%S")
                item["opening_hours"] = oh.as_opening_hours()
            except:
                self.crawler.stats.inc_value("atp/mkrf/failed_to_parse_hours")

    def parse_museum_types(self, item, poi_attributes):
        if poi_attributes.get("category", {}).get("sysName") == "muzei-i-galerei":
            if types := poi_attributes.get("extraFields", {}).get("types"):
                for type in types:
                    if value := MUSEUM_TYPES.get(type):
                        apply_category({"museum": value}, item)
                    else:
                        self.crawler.stats.inc_value(f"atp/mkrf/museum_types/failed/{type}")
