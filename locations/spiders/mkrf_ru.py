import scrapy
from scrapy.spiders import Spider
from scrapy.http import Request
from locations.categories import Categories, apply_category

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, DAYS

# TODO: cultural ceters, theaters, schools, libraries
CATEGORY_MAPPING = {
    "kinoteatry": Categories.CINEMA,
    "muzei-i-galerei": Categories.MUSEUM,
}


class MkrfRUSpider(Spider):
    name = "mkrf_ru"
    allowed_domains = ["opendata.mkrf.ru"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True
    # TODO: add more datasets from https://opendata.mkrf.ru/item/api
    datasets = [
                    "cinema",
                    "museums"
                ]
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

            if address := get_or_default(poi_attributes, "address"):
                item["street_address"] = address.get("street")
                item["addr_full"] = address.get("fullAddress")
                if coordinates := get_or_default(address, "mapPosition", "coordinates"):
                    item["lat"] = coordinates[1]
                    item["lon"] = coordinates[0]

            if contacts := get_or_default(poi_attributes, "contacts"):
                item["email"] = contacts.get("email")
                item["website"] = contacts.get("website")
                if phones := contacts.get("phones"):
                    item["phone"] = "; ".join([phone["value"] for phone in phones])

            item["image"] = get_or_default(poi_attributes, "image", "url")
            self.parse_category(item, poi_attributes)
            self.parse_hours(item, poi_attributes)

            # TODO: parse more attributes: social links, 

            yield item

    def parse_category(self, item, poi_attributes):
        if category := get_or_default(poi_attributes, "category"):
            if category_tag := CATEGORY_MAPPING.get(category.get("sysName", {})):
                apply_category(category_tag, item)

    def parse_hours(self, item, poi_attributes):
        if workingSchedule := poi_attributes.get("workingSchedule"):
            try:
                oh = OpeningHours()
                for k, v in workingSchedule.items():
                    oh.add_range(DAYS[int(k)], v.get("from"), v.get("to"), "%H:%M:%S")
                item["opening_hours"] = oh.as_opening_hours()
            except:
                self.crawler.stats.inc_value("failed_to_parse_hours")


def get_or_default(d, *keys, default=None):
    try:
        for k in keys:
            d = d[k]
    except (KeyError, IndexError):
        return default
    return d
