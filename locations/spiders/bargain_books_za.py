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
        for province_div in response.xpath('.//div[@class="et_pb_code_inner"]'):
            province = province_div.xpath(".//h2/text()").get()
            for location in province_div.xpath('.//tbody[@class="row-hover"]/tr'):
                item = Feature()
                item["branch"] = location.xpath('.//td[@class="column-1"]/text()').get()
                item["phone"] = location.xpath('.//td[@class="column-2"]/text()').get()
                addresses = location.xpath('.//td[@class="column-3"]/text()').getall()
                item["addr_full"] = clean_address([addresses[0], province])
                item["state"] = province
                if len(addresses) > 2:
                    item["email"] = addresses[2].replace("\n", "")

                item["opening_hours"] = OpeningHours()
                for day, column in [("Monday-Thursday ", "4"), ("Friday ", "5"), ("Saturday ", "6"), ("Sunday ", "7")]:
                    try:
                        item["opening_hours"].add_ranges_from_string(
                            day + location.xpath(f'.//td[@class="column-{column}"]/text()').get()
                        )
                    except TypeError:  # In case a cell is blank
                        pass

                yield item
