import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DhlExpressDeSpider(scrapy.Spider):
    name = "dhl_express_de"
    item_attributes = {"brand": "DHL", "brand_wikidata": "Q489815"}
    allowed_domains = ["dhl.de", "locator.dhl.com", "wsbexpress.dhl.com"]
    start_urls = ["https://www.dhl.de/en/geschaeftskunden/express/kontakt-express/dhl-express-stationen.html"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        urls = response.xpath('//a[contains(@href,"results?")]')
        for url in urls:
            id_location = re.findall(r"id:[-\w]+", url.xpath("./@href").get())[0][3:]
            url = f"https://wsbexpress.dhl.com/ServicePointLocator/restV3/servicepoints?servicePointResults=10&servicePointID={id_location}&languageScriptCode=Latn&language=eng&languageCountryCode=DE&resultUom=km&key=963d867f-48b8-4f36-823d-88f311d9f6ef"
            yield scrapy.Request(url=url, callback=self.parse_location)

    def parse_location(self, response):
        data = response.json().get("servicePoints")[0]
        item = DictParser.parse(data.get("address"))
        item["ref"] = data.get("facilityId")
        item["name"] = data.get("localName")
        item["lat"] = data.get("geoLocation", {}).get("latitude")
        item["lon"] = data.get("geoLocation", {}).get("longitude")
        item["phone"] = data.get("contactDetails", {}).get("phoneNumber")
        item["website"] = f'https://{data.get("contactDetails", {}).get("linkUri")}'
        oh = OpeningHours()
        for day in data.get("openingHours", {}).get("openingHours"):
            oh.add_range(day=day.get("dayOfWeek"), open_time=day.get("openingTime"), close_time=day.get("closingTime"))
        item["opening_hours"] = oh.as_opening_hours()

        apply_category(Categories.POST_OFFICE, item)

        yield item
