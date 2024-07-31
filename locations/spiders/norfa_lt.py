import chompjs
from scrapy import Spider

from locations.hours import DAYS_LT, OpeningHours
from locations.items import Feature


class NorfaLTSpider(Spider):
    name = "norfa_lt"
    start_urls = ["https://www.norfa.lt/parduotuves/"]
    item_attributes = {"brand": "Norfa", "brand_wikidata": "Q1998983"}

    def parse(self, response):
        js = (
            response.xpath("//script[contains(text(), '_markers_data_main ')]")
            .get()
            .replace(" var _markers_data_main = ", "")
        )
        data = chompjs.parse_js_object(js)

        for location in response.xpath("//div[contains(@class, 'c-shop shop-')]"):
            item = Feature()
            item["ref"] = location.xpath("@class").get().split("c-shop shop-")[1]

            for extra_data in data:
                if str(extra_data["id"]) == item["ref"]:
                    item["lat"] = extra_data["lat"]
                    item["lon"] = extra_data["lang"]

            item["street_address"] = location.xpath("*[@class='c-shop__location']/text()").get()
            item["opening_hours"] = OpeningHours()
            # I-VI 8.00-21.00 VII 10.00-20.00
            hours_str = location.xpath("*[@class='c-shop__hours']/text()").get().replace(".", ":")
            item["opening_hours"].add_ranges_from_string(hours_str, days=DAYS_LT)

            item["phone"] = location.xpath(
                "div/div[@class='c-shop-deatiled']/p/a[contains(@href, 'tel:')]/text()"
            ).get()

            # TODO: Is it worth mapping any of
            # <table class="c-services-table">
            # <td><i class="icon-fresh-food"></i></td>
            # <td>Karštų gaminių skyrius</td>
            # <td><i class="icon-fish"></i></td>
            # <td>Šviežios žuvies skyrius</td>
            # h<td><i class="icon-conditery"></i></td>
            # <td>Norfos kepyklėlė</td>

            yield item
