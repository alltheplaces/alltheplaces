import scrapy
import geonamescache
from locations.hours import OpeningHours, DAYS_FR
from locations.items import Feature
import re

class GeoxSpider(scrapy.Spider):
    name = "gamma"
    item_attributes = {"brand": "Geox", "brand_wikidata": "Q588001"}

    def start_requests(self):
        url = "https://www.geox.com/on/demandware.store/Sites-francese-Site/fr_FR/Stores-FindStoresAjax?countryCode={country_code}&page=storelocator&format=ajax"
        country_codes = geonamescache.GeonamesCache().get_countries().keys()
        for code in country_codes:
            yield scrapy.Request(url=url.format(code), callback=self.parse)

    def parse(self, response):
        data = response.json()
        for store in data["stores"]:
            item = Feature()
            item["ref"] = store["storeId"]
            item["name"] = "Geox " + store["name"]
            item["street_address"] = store["address"]
            item["city"] = store["city"]
            item["email"] = store["email"]
            item["phone"] = store["phone"]
            item["postcode"] = store["postalCode"]
            item["country"] = store["countryCode"]
            item["lat"] = store["lat"]
            item["lon"] = store["long"]
            item["website"] = "https://www.geox.com/fr-FR/storedetails?StoreID=" + store["storeId"]
            item["opening_hours"] = self.parse_opening_hours(store)

    def parse_opening_hours(self, store):
        oh = OpeningHours()
        store_oh = store["storeHours"]
        get_list = re.findall('(<p>)(.+?)(</p>)', store_oh)
        for elmt in get_list:
            oh.add_ranges_from_string(ranges_string=elmt[1], days=DAYS_FR, delimiters=[' - '])

        return oh.as_opening_hours()