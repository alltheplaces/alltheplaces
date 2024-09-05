from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address

BANNER_CODE_MAPPING = {
    "GE": {"brand": "Giant Eagle", "brand_wikidata": "Q1522721"},
    "GX": {"brand": "Giant Eagle Express", "brand_wikidata": "Q1522721"},
    "GG": {"brand": "GetGo", "brand_wikidata": "Q5553766"},
    "MD": {"brand": "Market District", "brand_wikidata": "Q98550869"},
    "WG": {"brand": "WetGo"},
}

TYPE_CODE_MAPPING = {
    "CV": Categories.SHOP_CONVENIENCE,
    "CW": Categories.CAR_WASH,
    "FU": Categories.FUEL_STATION,
    "SM": Categories.SHOP_SUPERMARKET,
}


class GiantEagleUSSpider(Spider):
    name = "giant_eagle_us"
    API_URL = "https://www.gianteagle.com/api/sitecore/locations/getlocationlistvm?q=&orderBy=geo.distance(storeCoordinate,%20geography%27POINT(-97.68%2030.27)%27)%20asc&skip={}"
    items_per_page = 12  # api limit

    def start_requests(self):
        yield self.response_for_page(0)

    def response_for_page(self, page):
        return Request(url=self.API_URL.format(page), cb_kwargs={"page": page})

    @staticmethod
    def parse_hours(hours):
        o = OpeningHours()
        for h in hours:
            if h["IsClosedAllDay"]:
                continue
            day_number = h["DayNumber"]
            if day_number == 7:
                day_number = 0
            day = DAYS[day_number]
            open_time = h["Range"].get("Open")
            close_time = h["Range"].get("Close")
            if h["IsOpenedAllDay"]:
                open_time = "0:00"
                close_time = "23:59"
            if open_time and close_time:
                o.add_range(day=day, open_time=open_time, close_time=close_time)
        return o

    @staticmethod
    def get_phone(store, line: str):
        if store.get("TelephoneNumbers"):
            for t in store["TelephoneNumbers"]:
                if t["location"]["Item2"] == line:
                    return t["DisplayNumber"]
        return None

    def parse(self, response, page):
        if stores := response.json()["Locations"]:
            for store in stores:

                type_code = store["Details"]["Type"]["Code"]
                self.crawler.stats.inc_value(f"atp/store/type/code/{type_code}")

                banner_code = store["Banner"]["Code"]
                self.crawler.stats.inc_value(f"atp/store/banner/code/{banner_code}")

                self.crawler.stats.inc_value(f"atp/store/combined/code/{banner_code}-{type_code}")

                store.update(store.pop("Address"))
                item = DictParser.parse(store)
                item["ref"] = store["Number"]["Value"]
                address_list = [store["address_no"], store["lineOne"], store["lineTwo"]]
                address_list = [x for x in address_list if x != "-"]
                item["street_address"] = clean_address(address_list)
                item["state"] = store["State"]["Abbreviation"]
                item["phone"] = self.get_phone(store, "Main")

                # The banner code gives us a brand.
                if brand_info := BANNER_CODE_MAPPING.get(banner_code):
                    item.update(brand_info)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/fail/banner_code/{banner_code}")
                    self.logger.error(f"unknown banner code: {banner_code}")
                    continue

                primary_category = TYPE_CODE_MAPPING.get(type_code)
                if not primary_category:
                    self.crawler.stats.inc_value(f"atp/{self.name}/fail/type_code/{type_code}")
                    self.logger.error(f"unknown type code: {type_code}")
                    continue

                # Some fuel locations will have subsidiary offerings such as a convenience store.
                if primary_category == Categories.FUEL_STATION:
                    if offerings := store.get("Offerings"):
                        if lobs := offerings.get("LineOfBusinesses"):
                            for lob in lobs:
                                if lob["Name"] == "Store":
                                    convenience_store = item.deepcopy()
                                    convenience_store["ref"] = str(item["ref"]) + "-CONVENIENCE"
                                    apply_category(Categories.SHOP_CONVENIENCE, convenience_store)
                                    convenience_store["opening_hours"] = self.parse_hours(lob["Hours"])
                                    yield convenience_store

                apply_category(primary_category, item)
                item["opening_hours"] = self.parse_hours(store["HoursOfOperation"])
                yield item

            yield self.response_for_page(page + self.items_per_page)
