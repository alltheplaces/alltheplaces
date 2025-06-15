from scrapy.http import JsonRequest
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import CLOSED_IT, DAYS_IT, DELIMITERS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class BccITSpider(JSONBlobSpider):
    name = "bcc_it"
    no_refs = True

    def start_requests(self):
        for lat, lon in country_iseadgg_centroids("IT", 24):
            yield JsonRequest(
                f"https://ws-annuario.service.gbi.bcc.it/Territorio.svc/REST/geosearch/bcc/sede,filiale,bancomat/{lat}/{lon}/25000/"
            )

    def pre_process_data(self, location):
        location["latitude"] = location.pop("LATITUDINE")
        location["longitude"] = location.pop("LONGITUDINE")

    def post_process_item(self, item, response, location):
        if location["TIPO"] == "FILIALE":
            apply_category(Categories.BANK, item)
            item["extras"]["atm"] = location["BANCOMAT"]
            if item["extras"]["atm"] in ["True", True]:
                item["extras"]["atm"] = "yes"
        elif location["TIPO"] == "BANCOMAT":
            apply_category(Categories.ATM, item)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/types/{location['TIPO']}")

        item["addr_full"] = location["DESTINAZIONE"]
        item["name"] = location["DENOMINAZIONE"]
        item["branch"] = location["NOME_SPORTELLO"]
        item["extras"]["wheelchair"] = location["ACCESSO_DISABILI"]
        if item["extras"]["wheelchair"] in ["True", True]:
            item["extras"]["wheelchair"] = "yes"

        if opening := location["ORARIO_APERTURA"]:
            times = " ".join(Selector(text=opening).css("*::text").getall())
            item["opening_hours"] = oh = OpeningHours()
            oh.add_ranges_from_string(
                times.replace(" e ", ", "),
                days=DAYS_IT,
                named_day_ranges=NAMED_DAY_RANGES_IT,
                named_times=NAMED_TIMES_IT,
                closed=CLOSED_IT,
                delimiters=DELIMITERS_IT,
            )
            if not oh:
                self.crawler.stats.inc_value(f"atp/{self.name}/weird_opening_hours_formatting")

        yield item
