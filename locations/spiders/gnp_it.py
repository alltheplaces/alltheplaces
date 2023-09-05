from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Access, Categories, Fuel, apply_category, apply_yes_no
from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.items import Feature


class GnpITSpider(Spider):
    name = "gnp_it"
    item_attributes = {"brand": "GNP", "brand_wikidata": "Q113950825"}

    def start_requests(self):
        yield JsonRequest(
            url="https://api.gnpfuel.it/api/v1/public/stations-query-by-prop", headers={"API-TOKEN": "V$MQ?UZB66$RT5"}
        )

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            if location["access"] != "public":
                continue

            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["coordinate"]["latitude"]
            item["lon"] = location["coordinate"]["longitude"]
            item["extras"]["branch"] = location["name"]
            item["street_address"] = location["address"]
            item["postcode"] = location["cap"]
            item["city"] = location["city"]
            item["state"] = location["province"]
            item["image"] = location["image"]
            item["website"] = urljoin("https://www.nordpetroli.it/distributori/", location["slug"])

            item["opening_hours"] = OpeningHours()
            for rule in location["opening"]:
                day = sanitise_day(rule.get("day"), DAYS_IT)
                if not day:
                    continue
                if rule.get("always_open"):
                    item["opening_hours"].add_range(day, "00:00", "23:59")
                else:
                    item["opening_hours"].add_range(day, rule.get("morning_from"), rule.get("morning_to"))
                    item["opening_hours"].add_range(day, rule.get("afternoon_from"), rule.get("afternoon_to"))

            # "highFlow" "self" "selfGPL" "serve" "serveGPL"
            apply_yes_no(Access.HGV, item, location["suitableForTruck"])

            # TODO: services
            # services = [s["name"] if s["active"] else None for s in location["services"]]

            fuels = [f["name"] for f in location["fuels"]]
            apply_yes_no(Fuel.ADBLUE, item, "AdBlue" in fuels)
            apply_yes_no(Fuel.OCTANE_95, item, "Benzina S.P." in fuels)
            apply_yes_no(Fuel.OCTANE_98, item, "Benzina S.P. 98" in fuels)
            apply_yes_no(Fuel.DIESEL, item, "Diesel" in fuels)

            apply_category(Categories.FUEL_STATION, item)

            yield item
