from locations.categories import Categories
from locations.items import Feature
from locations.spiders.opendata_mos_household_services_ru import OpendataMosSpider


class OpendataMosFoodRUSpider(OpendataMosSpider):
    name = "opendata_mos_food_ru"
    datasets = {"Food in Moscow": 1903}
    category_mapping = {
        "ресторан": Categories.RESTAURANT,
        "кафе": Categories.CAFE,
        "бар": Categories.BAR,
        "столовая": Categories.CANTEEN,
        "предприятие быстрого обслуживания": Categories.FAST_FOOD,
        "буфет": Categories.CAFE,
        "закусочная": Categories.FAST_FOOD,
        "кафетерий": Categories.CAFE,
        # Data from below category is wrongly categorized, ignore it
        "магазин (отдел кулинарии)": None,
    }

    # Exclude some branded locations as they already
    # captured by other spiders with better quality.
    def filter_function(self, row):
        row.get("Cells", {}).get("OperatingCompany") not in ["KFC", "Вкусно - и точка"]

    def parse_extra_fields(self, item: Feature, cells: dict):
        if seats_count := cells.get("SeatsCount"):
            item["extras"]["capacity"] = seats_count
