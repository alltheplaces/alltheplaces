import re

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.spiders.opendata_mos_household_services_ru import OpendataMosSpider

HOTEL_STARS_MAPPING = {
    "без звезд": None,
    "одна звезда": "1",
    "две звезды": "2",
    "три звезды": "3",
    "четыре звезды": "4",
    "пять звезд": "5",
}


class OpendataMosFoodRUSpider(OpendataMosSpider):
    name = "opendata_mos_hotels_ru"
    datasets = {"Classified Hotels and Other Accommodation Facilities": 2343}
    category_mapping = {
        "Апарт-отель": Categories.HOTEL,
        "Городская гостиница (отель)": Categories.HOTEL,
        "Гостиница, расположенная в здании, являющемся объектом культурного наследия или находящемся на территории исторического поселения": Categories.HOTEL,
        "Дома отдыха, пансионаты и другие аналогичные средства размещения": Categories.LEISURE_RESORT,
        "Загородный отель, туристская база, база отдыха": Categories.LEISURE_RESORT,
        "Комплекс апартаментов": Categories.TOURISM_APARTMENT,
        "Курортный отель, база отдыха, туристская база, центр отдыха, туристская деревня (деревня отдыха), дом отдыха, пансионат и другие аналогичные средства размещения": Categories.LEISURE_RESORT,
        "Курортный отель, санаторий, дом отдыха, центр отдыха, пансионат": Categories.LEISURE_RESORT,
        "Хостел": Categories.TOURISM_HOSTEL,
    }

    def parse_row(self, row: dict) -> Feature:
        cells = row.get("Cells", {})
        item = DictParser.parse(cells)
        item["ref"] = cells.get("global_id")
        item["name"] = cells.get("ObjectName")
        item["website"] = cells.get("WebSite")
        item["email"] = cells.get("Email")
        item["phone"] = cells.get("PublicPhone")
        item["street_address"] = item.pop("addr_full")
        item["lon"] = cells.get("geoData", {}).get("coordinates", [])[0]
        item["lat"] = cells.get("geoData", {}).get("coordinates", [])[1]
        item["extras"]["rooms"] = cells.get("RoomsQuantity")
        item["extras"]["beds"] = cells.get("PlacesQuantity")
        self.clean_legal_name(item)
        if stars := HOTEL_STARS_MAPPING.get(cells.get("AssignedCategory")):
            item["extras"]["stars"] = stars
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/stars/failed/{cells.get('AssignedCategory')}")

        return self.parse_category(item, cells.get("HotelType"))

    def clean_legal_name(self, item: Feature):
        """Clean company legal name string from name.
          e.g. 'Гостиница «Космос» ПАО «Гостиничный комплекс «Космос»' -> 'Гостиница «Космос»'
        It's hard to use these legal names as operators, as they are too inconsistent.
        """
        legal_abbreviations = ["ООО", "ОАО", "ЗАО", "ПАО", "ИП", "АО", "Общество с ограниченной ответственностью"]
        pattern = r"\s(" + "|".join(legal_abbreviations) + r")\s.*$"
        item["name"] = re.sub(pattern, "", item["name"]).strip()
