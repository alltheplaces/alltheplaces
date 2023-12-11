import html
import re

from scrapy import Request
from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.tesco_gb import set_located_in


class ArcoSpider(CSVFeedSpider):
    name = "arco"
    item_attributes = {"brand": "Arco", "brand_wikidata": "Q304769"}
    AMPM = {"brand": "ampm", "brand_wikidata": "Q306960"}

    def start_requests(self):
        yield Request("https://www.arco.com/scripts/stationfinder.js", self.parse_js)

    def parse_js(self, response, **kwargs):
        if match := re.search("var csv_url = '(.*)'", response.text):
            yield Request(response.urljoin(match.group(1)))

    def parse_row(self, response, row):
        if len(row["State"]) == 2 or row["State"] == "California":
            row["country_code"] = "US"
            row["street_address"] = html.unescape(row.pop("Address"))
        else:
            row["country_code"] = "MX"
            row["Address"] = html.unescape(row["Address"])

        arco = DictParser.parse(row)

        apply_yes_no(PaymentMethods.CREDIT_CARDS, arco, row["CreditCards"] == "1")
        apply_yes_no(Fuel.DIESEL, arco, row["CreditCards"] == "1")
        apply_yes_no(Extras.CAR_WASH, arco, row["CarWash"] == "1")
        # TODO: RenewableDiesel

        apply_category(Categories.FUEL_STATION, arco)

        yield arco

        if row["ampm"] == "1":
            ampm = DictParser.parse(row)
            ampm["ref"] += "_ampm"
            ampm["name"] = None
            ampm.update(self.AMPM)
            set_located_in(self.AMPM, ampm)

            yield ampm
