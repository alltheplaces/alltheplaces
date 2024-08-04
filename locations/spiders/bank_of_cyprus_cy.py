import html

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class BankOfCyprusCYSpider(scrapy.Spider):
    name = "bank_of_cyprus_cy"
    item_attributes = {"brand_wikidata": "Q806678"}
    start_urls = ["https://www.bankofcyprus.com/home-gr/bank_gr/storespage-gr/"]

    def parse(self, response):
        cities = response.xpath("//li[@class='cityMap']/@data-value").getall()
        for city in cities:
            yield scrapy.Request(
                f"https://www.bankofcyprus.com/ajax/StoresPage/GetFilteredStores?IsATMForeignCurrency=true&IsATMWithdrawals=true&IsATMDepositWithdrawals=true&IsStore=true&IsBCS=true&IsNotesCoins=true&isCoinDeposit=true&isCoinDispenser=true&Region={city}&SearchString=&Country=CY&Language=el",
                callback=self.parse_pois,
                cb_kwargs=dict(city=city),
            )

    def parse_pois(self, response, city):
        for poi in response.xpath("//li/div[@class='result-item']"):
            item = Feature()
            item["ref"] = poi.xpath('.//span[@class="number"]/text()').get().replace("\u00a0", "")
            item["street_address"] = poi.xpath(".//@data-address").get()
            item["city"] = city
            item["branch"] = html.unescape(poi.xpath(".//@data-name").get())
            item["lat"] = poi.xpath(".//@data-lat").get()
            item["lon"] = poi.xpath(".//@data-long").get()
            item["phone"] = poi.xpath(".//@data-phone").get()
            if "ATM" in item["branch"]:
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)
            yield item
