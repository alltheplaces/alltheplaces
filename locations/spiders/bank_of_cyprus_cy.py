import html

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class BankOfCyprusCYSpider(scrapy.Spider):
    name = "bank_of_cyprus_cy"
    item_attributes = {"brand_wikidata": "Q806678"}
    start_urls = ["https://www.bankofcyprus.com/home-gr/bank_gr/storespage-gr/"]
    no_refs = True

    def parse(self, response):
        cities = response.xpath("//option[@class='cityMap']/text()").getall()
        for city in cities:
            if city == "Όλες οι πόλεις":  # Skip "All cities" option
                continue
            yield scrapy.Request(
                f"https://www.bankofcyprus.com/ajax/StoresPage/GetFilteredStores?Region={city}&SearchString=&Country=CY&Language=el",
                callback=self.parse_pois,
                cb_kwargs=dict(city=city),
            )

    def parse_pois(self, response, city):
        for poi in response.xpath("//li/button[@class='result-item']"):
            item = Feature()
            item["street_address"] = poi.xpath(".//@data-address").get()
            item["city"] = city
            item["name"] = item["branch"] = html.unescape(poi.xpath(".//@data-name").get())
            item["lat"] = poi.xpath(".//@data-lat").get()
            item["lon"] = poi.xpath(".//@data-long").get()
            phone = poi.xpath(".//@data-tel").get()
            if phone:
                item["phone"] = phone.removeprefix("Tel: ")

            if "ATM" in item["branch"]:
                apply_category(Categories.ATM, item)
                apply_yes_no(Extras.CASH_IN, item, poi.xpath(".//@data-service-atm-deposit-withdrawals").get())
            else:
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, poi.xpath(".//@data-service-atm-deposit-withdrawals").get())
                apply_yes_no(Extras.CASH_IN, item, poi.xpath(".//@data-service-atm-deposit-withdrawals").get())

            yield item
