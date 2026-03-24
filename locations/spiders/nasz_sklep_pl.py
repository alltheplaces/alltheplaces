from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature


class NaszSklepPLSpider(Spider):
    name = "nasz_sklep_pl"
    brands = {
        "DS": {"brand": "Delikatesy Sezam", "brand_wikidata": "Q120173828"},
        "Livio": {"brand": "Livio", "brand_wikidata": "Q108599511"},
        "NS": {"brand": "Nasz Sklep", "brand_wikidata": "Q62070369"},
        "LU": {"brand": "Lubazo", "brand_wikidata": ""},
    }
    start_urls = ["https://nasz-sklep.pl/sklepy-wlasne/"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//table//tr[position()>1]"):

            store = location.xpath("td/text()").getall()
            item = Feature()
            if len(store) == 8:
                (
                    brand,
                    item["city"],
                    item["street_address"],
                    item["email"],
                    item["phone"],
                    mon_fri_hours,
                    saturday_hours,
                    sunday_hours,
                ) = store
            elif len(store) == 7:
                (
                    brand,
                    item["city"],
                    item["street_address"],
                    item["phone"],
                    mon_fri_hours,
                    saturday_hours,
                    sunday_hours,
                ) = store
                item["phone"] = None
            else:
                self.crawler.stats.inc_value("{}/unparsed_store_format".format(self.name))
                continue
            if brand not in ["Livio"]:
                brand = brand[:2]
            if b := self.brands.get(brand):
                item.update(b)
            else:
                self.crawler.stats.inc_value("{}/unmapped_brand/{}".format(self.name, brand))

            item["opening_hours"] = OpeningHours()
            mon_fri_start, mon_fri_end = mon_fri_hours.split("-")
            for day in DAYS_WEEKDAY:
                item["opening_hours"].add_range(day, mon_fri_start, mon_fri_end)
            sat_start, sat_end = saturday_hours.split("-")
            item["opening_hours"].add_range(DAYS_WEEKEND[0], sat_start, sat_end)
            if "Zamknięte" in sunday_hours:
                item["opening_hours"].set_closed(DAYS_WEEKEND[1])
            else:
                sun_start, sun_end = sunday_hours.split("-")
                item["opening_hours"].add_range(DAYS_WEEKEND[1], sun_start, sun_end)
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
