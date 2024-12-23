from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BargainBooksZASpider(Spider):
    name = "bargain_books_za"
    item_attributes = {"brand": "Bargain Books", "brand_wikidata": "Q116741024"}
    start_urls = ["https://www.bargainbooks.co.za/store-locator/"]
    no_refs = True

    def parse(self, response):
        for store in response.xpath('//tbody/tr'):
            item = Feature()
            item["branch"] = store.xpath('.//td[@class="column-1"]/text()').get()
            item["phone"] = store.xpath('.//td[@class="column-2"]/text()').get()
            item["addr_full"] = store.xpath('.//td[@class="column-3"]/text()[1]').get()
            item["website"] = "https://www.bargainbooks.co.za/"
            if email:= store.xpath('.//td[@class="column-3"]/text()[2]').get():
                item["email"] = email
            item["opening_hours"] = OpeningHours()
            for day, column in [("Monday-Thursday ", "4"), ("Friday ", "5"), ("Saturday ", "6"), ("Sunday ", "7")]:
                try:
                    item["opening_hours"].add_ranges_from_string(
                        day + store.xpath(f'.//td[@class="column-{column}"]/text()').get()
                    )
                except TypeError:  # In case a cell is blank
                    pass

            yield item
