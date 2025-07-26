from html import unescape
from typing import Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_ID, OpeningHours
from locations.items import Feature
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaIDSpider(Spider):
    name = "mazda_id"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    allowed_domains = ["mazda.co.id"]
    start_urls = ["https://mazda.co.id/find-a-dealers"]

    def parse(self, response: Response) -> Iterable[Feature]:
        js_blob = response.xpath('//script[contains(text(), "function getdealer(){")]/text()').get()
        js_blob = js_blob.split("function getdealer(){", 1)[1].strip().removesuffix("}").strip()
        dealers = {}
        variable_map = {
            "dealerId": "ref",
            "dealerName": "branch",
            "dealerAddress": "address",
            "dealerPhone": "phone",
            "dealersalesOperationalHour": "hours_sales",
            "dealerserviceOperationalHour": "hours_service",
        }
        for line in js_blob.splitlines():
            line = line.strip()
            for variable_name, atp_field_name in variable_map.items():
                if line.startswith(variable_name):
                    dealer_dict_key = line.split("[", 1)[1].split("]", 1)[0]
                    variable_value = unescape(line.split("'", 1)[1].split("'", 1)[0])
                    if dealer_dict_key not in dealers.keys():
                        dealers[dealer_dict_key] = {}
                    dealers[dealer_dict_key][atp_field_name] = variable_value
                    break
                elif line.startswith("dealerLat"):
                    # "dealerLat" is accidentally misnamed on the second
                    # statement, meaning the original latitude is overwritten
                    # and no longitude is set. A workaround is required to
                    # extract both lat and lon.
                    dealer_dict_key = line.split("[", 1)[1].split("]", 1)[0]
                    variable_value = unescape(line.split("'", 1)[1].split("'", 1)[0])
                    if dealer_dict_key not in dealers.keys():
                        dealers[dealer_dict_key] = {}
                    if "lat" not in dealers[dealer_dict_key].keys():
                        dealers[dealer_dict_key]["lat"] = variable_value
                    else:
                        dealers[dealer_dict_key]["lon"] = variable_value
                    break

        for dealer in dealers.values():
            item = DictParser.parse(dealer)
            item["branch"] = dealer["branch"].removeprefix("Mazda ")
            hours_sales_text = " ".join(Selector(text=dealer["hours_sales"]).xpath("//text()").getall())
            hours_service_text = " ".join(Selector(text=dealer["hours_service"]).xpath("//text()").getall())
            if hours_sales_text:
                sales_item = item.deepcopy()
                sales_item["ref"] = sales_item["ref"] + "_Sales"
                sales_item["opening_hours"] = OpeningHours()
                sales_item["opening_hours"].add_ranges_from_string(hours_sales_text, days=DAYS_ID)
                apply_category(Categories.SHOP_CAR, sales_item)
                yield sales_item
            if hours_service_text:
                service_item = item.deepcopy()
                service_item["ref"] = service_item["ref"] + "_Service"
                service_item["opening_hours"] = OpeningHours()
                service_item["opening_hours"].add_ranges_from_string(hours_service_text, days=DAYS_ID)
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item
