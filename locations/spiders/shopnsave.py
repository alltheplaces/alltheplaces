import re

import scrapy

from locations.items import Feature

DAY_DICT = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Thurs": "Th",
    "Thur": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
    "24 hours/7 days a week": "24/7",
    "Please contact store for hours": "N/A",
}


class ShopnsaveSpider(scrapy.Spider):
    name = "shopnsave"
    item_attributes = {"brand": "SHOP ‘n SAVE"}
    allowed_domains = ["www.shopnsave.com"]
    start_urls = (
        "https://www.shopnsave.com/stores/view-stores-by-state.html?state=IL&page=1",
        "https://www.shopnsave.com/stores/view-stores-by-state.html?state=IL&page=2",
        "https://www.shopnsave.com/stores/view-stores-by-state.html?state=MO&page=1",
        "https://www.shopnsave.com/stores/view-stores-by-state.html?state=MO&page=2",
        "https://www.shopnsave.com/stores/view-stores-by-state.html?state=MO&page=3",
    )

    def parse(self, response):
        stores = response.xpath('//table[@id="store-search-result"]/tbody/tr[@class="" or @class="store-grey"]')
        for store in stores:
            properties = {
                "ref": store.xpath('td[@class="store-result-address"]/text()').extract_first(),
                "name": store.xpath('td[@class="store-result-address"]/text()').extract_first(),
                "opening_hours": self.store_hours(
                    store.xpath('td[@class="store-result-address"]/text()[last()-1]').extract_first()
                ),
                "addr_full": store.xpath('td[@class="store-result-address"]/text()')[1].extract(),
                "city": self.city(store.xpath('td[@class="store-result-address"]/text()')[2].extract()),
                "state": self.state(store.xpath('td[@class="store-result-address"]/text()')[2].extract()),
                "postcode": self.post_code(store.xpath('td[@class="store-result-address"]/text()')[2].extract()),
                "phone": self.phone(store.xpath('td[@class="store-result-phone"]/strong/text()')[0].extract()),
            }

            yield Feature(**properties)

    def city(self, data):
        str_list = data.split(",")
        return str_list[0].strip()

    def state(self, data):
        str_list = data.split(",")
        state = str_list[1].strip()
        state = state[:2]
        return state

    def post_code(self, data):
        str_list = data.split(",")
        zip_code = str_list[1].strip()
        return zip_code[-5:]

    def phone(self, data):
        return data.replace("— Main", "")

    def store_hours(self, store_hours):
        if "day" not in store_hours and "-" not in store_hours:
            return ""

        if "24 Hours, 7 days a week" in store_hours:
            return "24/7"
        store_hours = store_hours.replace("\r\n\t\t\t\t\t\t", "")
        store_hours = store_hours.replace("Midnight", "00:00")

        pattern = re.compile(r"\b(" + "|".join(DAY_DICT.keys()) + r")\b")
        store_hours = pattern.sub(lambda x: DAY_DICT[x.group()], "".join(store_hours))
        store_hours = store_hours.replace("am", ":00")

        m = re.search(r"([0-9]{1,2})(\spm)", store_hours)
        if m:
            h = m.group(1)
            new_h = int(h) + 12
            store_hours = store_hours.replace(h + " pm", str(new_h) + ":00")

        return store_hours
