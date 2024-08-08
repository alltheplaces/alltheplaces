import scrapy
from scrapy.http import JsonRequest, Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, OpeningHours
from locations.items import Feature

CATEGORY_MAPPING = {
    "ремонт телефонов, планшетов": Categories.CRAFT_ELECTRONICS_REPAIR.value | {"electronics_repair": "phone"},
    "автомойка": Categories.CAR_WASH,
    "детейлинг": Categories.SHOP_CAR_REPAIR.value | {"service": "detailing"},
    "изготовление и ремонт мебели": Categories.CRAFT_CARPENTER,
    "косметические услуги": Categories.SHOP_BEAUTY,
    "парикмахерская": Categories.SHOP_HAIRDRESSER,
    "парикмахерские и косметические услуги": Categories.SHOP_BEAUTY,
    "прачечные самообслуживания": Categories.SHOP_LAUNDRY.value | {"self_service": "yes"},
    "прачечные самообслуживания (стирка и глажение методом самообслуживания)": Categories.SHOP_LAUNDRY.value
    | {"self_service": "yes", "dry_cleaning": "yes"},
    "приемный пункт в химчистку и стирку": Categories.SHOP_DRY_CLEANING,
    "ремонт бытовой техники (холодильники, стиральные машины, телевизоры и другие)": Categories.CRAFT_ELECTRONICS_REPAIR.value
    | {"repair": "appliance"},
    "ремонт и изготовление металлоизделий": Categories.CRAFT_KEY_CUTTER,
    "ремонт и изготовление металлоизделий (ключей, зонтов, замков, заточка коньков и другие)": Categories.CRAFT_KEY_CUTTER,
    "ремонт и пошив швейных, меховых и кожаных изделий, головных уборов и изделий текстильной галантереи, ремонт, пошив и вязание трикотажных изделий": Categories.CRAFT_TAILOR,
    "ремонт и техническое обслуживание бытовой радиоэлектронной аппаратуры, бытовых машин и бытовых приборов, техники": Categories.CRAFT_ELECTRONICS_REPAIR.value
    | {"repair": "appliance"},
    "ремонт иных видов техники (садовая, стартеры, генераторы, климат системы и другие)": Categories.CRAFT_ELECTRONICS_REPAIR.value
    | {"repair": "appliance"},
    "ремонт компьютеров, радиоэлектронной аппаратуры": Categories.CRAFT_ELECTRONICS_REPAIR.value
    | {"electronics_repair": "computer"},
    "ремонт спортивного инвентаря (велосипеды, самокаты, электроскутеры и другие)": Categories.SHOP_BICYCLE.value
    | {"service:bicycle:repair": "yes", "service:bicycle:retail": "no"},
    "ремонт часов": Categories.CRAFT_CLOCKMAKER,
    "ремонт ювелирных изделий": Categories.CRAFT_JEWELLER,
    "ремонт, окраска и пошив обуви": Categories.CRAFT_SHOEMAKER,
    "ритуальные и обрядовые услуги": Categories.SHOP_FUNERAL_DIRECTORS,
    "стирка белья (прачечные)": Categories.SHOP_LAUNDRY,
    "татуаж": Categories.SHOP_BEAUTY,
    "техническое обслуживание и ремонт транспортных средств": Categories.SHOP_CAR_REPAIR,
    "услуги багетных и зеркальных мастерских": Categories.SHOP_FRAME,
    "услуги бань": Categories.SAUNA,
    "услуги ломбарда": Categories.SHOP_PAWNBROKER,
    "услуги ногтевого сервиса (маникюр, педикюр)": Categories.SHOP_BEAUTY.value | {"beauty": "nails"},
    "услуги саун": Categories.SAUNA,
    "фабрика - прачечная, прачечная (стирка - производство)": Categories.SHOP_LAUNDRY,
    "фото и копировальные услуги, малая полиграфия": Categories.SHOP_COPYSHOP,
    "фотоателье, фотоуслуги": Categories.SHOP_PHOTO,
    "химическая чистка и крашение": Categories.SHOP_DRY_CLEANING,
    "химчистка - прачечная (химчистка и стирка - производство)": Categories.SHOP_DRY_CLEANING,
    "химчистка методом самообслуживания": Categories.SHOP_DRY_CLEANING.value | {"self_service": "yes"},
    "химчистки самообслуживания": Categories.SHOP_DRY_CLEANING.value | {"self_service": "yes"},
    "шиномонтаж": Categories.SHOP_CAR_REPAIR.value | {"service": "tyres", "service:vehicle:tyres": "yes"},
    # TODO: categorize
    "услуги профессиональной уборки - клининговые услуги": None,
    # Below types are too broad to categorize
    "услуги проката": None,
    "иные объекты бытового обслуживания": None,
    "комплексное предприятие бытового обслуживания": None,
}


class OpendataMosSpider(scrapy.Spider):
    """
    A spider for Open Data Portal of Moscow Government.
        Documentation: https://data.mos.ru/developers
        More datasets: https://data.mos.ru/
    Each dataset from this portal may have different data format.
    """

    allowed_domains = ["apidata.mos.ru"]
    api_key = "8caab471-cc9f-46c8-aeea-fa3f5e1c765c"
    download_delay = 0.25
    requires_proxy = True
    dataset_attributes = {
        "attribution": "required",
        "attribution:name:ru": "ПОРТАЛ ОТКРЫТЫХ ДАННЫХ Правительства Москвы",
        "attribution:name:en": "OPEN DATA PORTAL of Moscow Government",
        "attribution:website": "https://data.mos.ru/",
        "contact:email": "opendata@mos.ru",
        "license": "Creative Commons Attribution 3.0 Unported",
        "license:website": "https://creativecommons.org/licenses/by/3.0/",
        "license:wikidata": "Q14947546",
        "use:commercial": "permit",
    }
    datasets = {}
    category_mapping = {}

    def filter_function(self, row):
        return row

    def start_requests(self):
        for name, id in self.datasets.items():
            yield Request(
                url=f"https://apidata.mos.ru/v1/datasets/{id}/count?api_key={self.api_key}",
                meta={"id": id, "name": name},
            )

    def parse(self, response):
        id = response.meta["id"]
        name = response.meta["name"]
        count = int(response.text)
        self.logger.info(f"Found {count} rows in dataset {name}(id={id})")
        for offset in range(0, count, 500):
            # a max number of rows to fetch is top=500
            yield JsonRequest(
                url=f"https://apidata.mos.ru/v1/datasets/{id}/rows?$top=500&$skip={offset}&api_key={self.api_key}",
                callback=self.parse_data,
            )

    def parse_data(self, response):
        for row in self.filter_rows(response.json()):
            yield self.parse_row(row)

    def filter_rows(self, rows: list) -> list:
        filtered = list(filter(self.filter_function, rows))
        self.crawler.stats.inc_value("atp/opendata_mos_ru/filter", len(rows) - len(filtered))
        return filtered

    def parse_row(self, row: dict) -> Feature:
        cells = row.get("Cells", {})
        item = DictParser.parse(cells)
        item["lat"] = cells.get("Latitude_WGS84")
        item["lon"] = cells.get("Longitude_WGS84")
        item["operator"] = cells.get("OperatingCompany")
        self.parse_phones(item, cells)
        self.parse_hours(item, cells)
        self.parse_extra_fields(item, cells)
        return self.parse_category(item, cells.get("TypeObject"))

    def parse_category(self, item: Feature, category: str):
        if tags := self.category_mapping.get(category):
            apply_category(tags, item)
            return item
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/category/failed/{category}")
            return None

    def parse_phones(self, item: Feature, cells: dict):
        if phones := cells.get("PublicPhone"):
            item_phones = []
            for phone in phones:
                deleted = phone.get("is_deleted")
                number = phone.get("PublicPhone")
                if deleted == 0 and number != "нет телефона":
                    item_phones.append(number)
            if item_phones:
                item["phone"] = "; ".join(item_phones)

    def parse_hours(self, item: Feature, cells: dict):
        # TODO: parse ClarificationOfWorkingHours
        if hours := cells.get("WorkingHours"):
            try:
                oh = OpeningHours()
                for hour in hours:
                    if hour.get("is_deleted") == 0:
                        if times := hour.get("Hours"):
                            if times == "выходной":  # day off
                                continue
                            if times == "круглосуточно":  # 24 hours
                                times = "00:00-24:00"
                            day = DAYS_RU.get(hour.get("DayOfWeek", "").title())
                            times = times.split("-")
                            open, close = times[0], times[1]
                            oh.add_range(day, open, close)
                item["opening_hours"] = oh.as_opening_hours()
            except Exception:
                self.logger.warning(f"Parse hours failed: {hours}")
                self.crawler.stats.inc_value("atp/opendata_mos_ru/hours/failed")

    def parse_extra_fields(self, item: Feature, cells: dict):
        pass


class OpendataMosHouseholdServicesRUSpider(OpendataMosSpider):
    name = "opendata_mos_household_services_ru"
    datasets = {"Household services in Moscow": 1904}
    category_mapping = CATEGORY_MAPPING
