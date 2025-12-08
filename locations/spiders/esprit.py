import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class EspritSpider(scrapy.Spider):
    name = "esprit"
    start_urls = ["https://www.esprit.com/interface/service-storefinder.php?query=getallstores"]

    item_attributes = {"brand": "Esprit", "brand_wikidata": "Q532746"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for store in response.json():
            # 1: Esprit stores
            # 2: Esprit franchise stores
            # 5: Esprit outlet stores
            if store.get("store_type_id") not in ("1", "2", "5"):
                continue
            oh = OpeningHours()
            for i, hours in enumerate(store.get("opening_times")):
                if hours.get("open") == 0:
                    continue
                opening = hours.get("from")
                closing = hours.get("until")
                oh.add_range(
                    day=DAYS[i],
                    open_time=f"{opening.get('h')}:{opening.get('m')}",
                    close_time=f"{closing.get('h')}:{closing.get('m')}",
                    time_format="%H:%M",
                )
            store["street_address"] = clean_address([store["address_additional"], store.pop("address")])
            item = DictParser.parse(store)
            item["lat"] = store.get("geo_latitude")
            item["lon"] = store.get("geo_longitude")
            item["website"] = (
                f'https://www.esprit.com/storefinder?storeid={store["store_id"]}&location={store["geo_latitude"]},{store["geo_longitude"]}'
            )
            item["opening_hours"] = oh
            yield item
