import json

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class BancoBpmITSpider(scrapy.Spider):
    name = "banco_bpm_it"
    item_attributes = {"brand": "Banco BPM", "brand_wikidata": "Q27331643"}
    start_urls = ["https://www.bancobpm.it/trova-filiali/"]

    def parse(self, response, **kwargs):
        data_raw = response.xpath('//script[@id="__NEXT_DATA__" and @type="application/json"]/text()').get()
        branch_data = json.loads(data_raw)["props"]["pageProps"]["page"]["filiali"]
        for branch in branch_data:
            item = DictParser.parse(branch)
            item["ref"] = branch["CodFiliale"]
            item["branch"] = branch["Nome_Banca"].replace("Banco BPM - ", "")
            item["street_address"] = branch["Indirizzo"]
            item["city"] = branch["Comune"]
            item["postcode"] = branch["Cap"]
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, branch["Bancomat"] == "SI")
            yield item
