from chompjs import parse_js_object
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class DomayneAUSpider(Spider):
    name = "domayne_au"
    item_attributes = {"brand": "Domayne", "brand_wikidata": "Q106224590"}
    allowed_domains = ["stores.domayne.com.au"]
    start_urls = ["https://stores.domayne.com.au/"]
    # robots.txt returns a HTTP error page that causes parsing errors
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        js_blob = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        json_blob = parse_js_object(js_blob)
        locations = json_blob["props"]["pageProps"]["locations"]
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["storeCode"]
            item["street_address"] = clean_address(location["addressLines"])
            if location.get("phoneNumbers") and len(location["phoneNumbers"]) == 1:
                item["phone"] = location["phoneNumbers"][0]
            if item["website"]:
                item["website"] = item["website"].replace(".au//", ".au/")
            item["opening_hours"] = OpeningHours()
            for day_number, day_hours in enumerate(location.get("businessHours", [])):
                if len(day_hours) != 2:
                    continue
                item["opening_hours"].add_range(DAYS_3_LETTERS_FROM_SUNDAY[day_number], day_hours[0], day_hours[1])
            yield item
