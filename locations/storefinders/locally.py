import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class LocallySpider(scrapy.Spider):
    allowed_domains = []
    start_urls = []
    api_key = None  # Later, will refactor to this
    custom_settings = {"ROBOTSTXT_OBEY": False}
    # "https://www.locally.com/stores/conversion_data?has_data=true&company_id=1682&store_mode=&style=&color=&upc=&category=&inline=1&show_links_in_list=&parent_domain=&map_center_lat=31.945163222857545&map_center_lng=-96.352774663203&map_distance_diag=2692.1535387671056&sort_by=proximity&no_variants=0&only_retailer_id=&dealers_company_id=&only_store_id=false&uses_alt_coords=false&q=false&zoom_level=5"
    # "https://crocs.locally.com/stores/conversion_data?has_data=true&company_id=1762&category=Store&inline=1&map_center_lat=46.661219&map_center_lng=2.587603&map_distance_diag=3000&sort_by=proximity&lang=en-gb",

    def parse(self, response):
        for store in response.json()["markers"]:
            oh = OpeningHours()
            item = DictParser.parse(store)
            self.pre_process_item(item, store)
            for day in DAYS_FULL:
                open = f"{day[:3].lower()}_time_open"
                close = f"{day[:3].lower()}_time_close"
                if not store.get(open) or len(str(store.get(open))) < 3:
                    continue
                oh.add_range(
                    day=day,
                    open_time=f"{str(store.get(open))[:-2]}:{str(store.get(open))[-2:]}",
                    close_time=f"{str(store.get(close))[:-2]}:{str(store.get(close))[-2:]}",
                )
            item["opening_hours"] = oh.as_opening_hours()
            self.post_process_item(item, store)
            yield item

    def pre_process_item(self, item, store):
        yield item

    def post_process_item(self, item, store):
        yield item
