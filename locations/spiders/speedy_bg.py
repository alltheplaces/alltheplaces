from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_BG, OpeningHours
from locations.items import Feature


class SpeedyBGSpider(Spider):
    name = "speedy_bg"
    item_attributes = {"brand": "Speedy", "brand_wikidata": "Q131312685"}
    allowed_domains = ["speedy.bg"]
    start_urls = ["https://services.speedy.bg/officesmap_v2/?src=sws"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script_obj = response.xpath('//script[contains(text(), "var speedy_offices =")]/text()').get("")
        if not script_obj:
            return

        object_str = script_obj.split("var speedy_offices = ")[1].split(";")[0]
        locations = chompjs.parse_js_object(object_str)

        for location in locations.values():
            item = Feature()
            item["ref"] = location["oID"]
            item["lat"] = location["Y"]
            item["lon"] = location["X"]

            if location["officeType"] == "APT":
                item["name"] = location["officeName"].removesuffix(" (АВТОМАТ)")
                apply_category(Categories.PARCEL_LOCKER, item)
            else:
                item["name"] = location["officeName"]
                apply_category(Categories.POST_OFFICE, item)

            yield JsonRequest(
                "https://services.speedy.bg/officesmap_v2/classBuilder.php",
                data={
                    "class": "",
                    "function": "bubbleHtmlFiller",
                    "arguments": {
                        "id": str(location["oID"]),
                        "selectOfficeButtonCaption": "",
                        "textButtonImage": "Снимка",
                        "textDirections": "упътвания",
                        "src": "sws",
                    },
                    "lang": "bg",
                },
                callback=self.parse_extra_info,
                cb_kwargs={"item": item},
            )

    def parse_extra_info(self, response: Response, item: Feature) -> Any:
        item["addr_full"] = response.xpath("//div[@class='divOfficeAddress']/text()").get()

        oh_boxes = response.xpath("//div[@class='divWtBlock']")
        oh = OpeningHours()
        for box in oh_boxes:
            box_title = box.xpath(".//div[@class='divWtTitle']/text()").get()
            if box_title != "Работно време:":
                continue
            rows = box.xpath(".//div[@class='divWtRow']")
            for row in rows:
                days = row.xpath(".//div[@class='divWtDay']/text()").get()
                hours = row.xpath(".//div[@class='divWtHours']/text()").get()
                oh.add_ranges_from_string(f"{days} {hours}", DAYS_BG)

        item["opening_hours"] = oh

        cash_payment = response.xpath("boolean(//img[@href='images/iconCashPayment.svg'])").get()
        card_payment = response.xpath("boolean(//img[@href='images/iconCardPayment.svg'])").get()
        apply_yes_no("payment:cash", item, cash_payment)
        apply_yes_no("payment:cards", item, card_payment)

        yield item
