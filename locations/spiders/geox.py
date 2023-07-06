import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class GeoxSpider(scrapy.Spider):
    name = "geox"
    item_attributes = {"brand": "Geox", "brand_wikidata": "Q588001"}
    start_urls = ["https://www.geox.com/int/stores"]

    def parse(self, response):
        url = "https://www.geox.com/on/demandware.store/Sites-international-Site/en_GB/Stores-FindStoresAjax?countryCode={country_code}&page=storelocator&format=ajax"
        country_codes = response.xpath('//*[@id="dwfrm_storelocator_country"]/option/@value').getall()
        for code in country_codes:
            yield scrapy.Request(url=url.format(country_code=code), callback=self.parse_country)

    def parse_country(self, response):
        data = response.json()
        if data["stores"]:
            for store in data["stores"]:
                item = Feature()
                item["ref"] = store["storeId"]
                item["name"] = ("Geox " + (store.get("name") or "")).strip()
                item["street_address"] = store["address"]
                item["city"] = store["city"]
                item["email"] = store["email"]
                item["phone"] = store["phone"]
                item["postcode"] = store["postalCode"].strip()
                item["country"] = store["countryCode"]
                item["lat"] = store["lat"]
                item["lon"] = store["long"]
                item["website"] = "https://www.geox.com/int/storedetails?StoreID=" + store["storeId"]
                item["opening_hours"] = self.parse_opening_hours(store)
                yield item

    @staticmethod
    def parse_opening_hours(store: dict) -> OpeningHours:
        oh = OpeningHours()
        store_oh = store["storeHours"]
        get_list = re.findall("(<p>)(.+?)(</p>)", store_oh)
        for elmt in get_list:
            oh.add_ranges_from_string(ranges_string=elmt[1], delimiters=[" - "])
        return oh
