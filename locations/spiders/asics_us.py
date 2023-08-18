import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class AsicsUsSpider(scrapy.Spider):
    name = "asics_us"
    item_attributes = {"brand": "asics", "brand_wikidata": "Q327247"}
    allowed_domains = ["www.asics.com"]
    start_urls = [
        "https://www.locally.com/stores/conversion_data?has_data=true&company_id=1682&store_mode=&style=&color=&upc=&category=&inline=1&show_links_in_list=&parent_domain=&map_center_lat=31.945163222857545&map_center_lng=-96.352774663203&map_distance_diag=2692.1535387671056&sort_by=proximity&no_variants=0&only_retailer_id=&dealers_company_id=&only_store_id=false&uses_alt_coords=false&q=false&zoom_level=5"
    ]

    def parse(self, response):
        for store in response.json()["markers"]:
            oh = OpeningHours()
            item = DictParser.parse(store)
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
            yield item
