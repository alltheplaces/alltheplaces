import json

from scrapy import Request, Spider

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class KfcJPSpider(Spider):
    name = "kfc_jp"
    item_attributes = {"brand_wikidata": "Q524757"}
    allowed_domains = ["search.kfc.co.jp"]
    start_urls = ["https://search.kfc.co.jp/api/point?b=31,129,46,146"]

    def parse(self, response):
        for location in response.json()["items"]:
            item = DictParser.parse(location)
            item["ref"] = location["key"]
            item["website"] = "https://search.kfc.co.jp/map/" + item["ref"]
            yield Request(url=item["website"], meta={"item": item}, callback=self.parse_hours)

    def parse_hours(self, response):
        item = response.meta["item"]
        data_raw = response.xpath("//script[contains(text(), \"angular.module('slApp')\")]/text()").get().split("\n")
        data_json = "{}"
        for constant in data_raw:
            if ".constant('CURRENT_POINT'" in constant:
                data_json = constant.split(".constant('CURRENT_POINT', ")[1][:-1]
                break
        location = json.loads(data_json)
        item2 = DictParser.parse(location)
        for key, value in item2.items():
            if value:
                item[key] = value

        apply_yes_no(Extras.DRIVE_THROUGH, item, location["ドライブスルー"], False)
        apply_yes_no(Extras.DELIVERY, item, location["お届けケンタッキー"], False)
        apply_yes_no(Extras.WIFI, item, location["無線LAN対応"], False)
        apply_yes_no(PaymentMethods.VISA, item, location["クレジットカード:VISA"], False)
        apply_yes_no(PaymentMethods.MASTER_CARD, item, location["クレジットカード:Master Card"], False)
        apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, location["クレジットカード:American Express"], False)
        apply_yes_no(PaymentMethods.DINERS_CLUB, item, location["クレジットカード:Diners Club"], False)
        apply_yes_no(PaymentMethods.JCB, item, location["クレジットカード:JCB"], False)
        apply_yes_no(PaymentMethods.PAYPAY, item, location["QRコード決済：PayPay"], False)
        apply_yes_no(PaymentMethods.LINE_PAY, item, location["QRコード決済：LINE Pay"], False)
        apply_yes_no(PaymentMethods.RAKUTEN_PAY, item, location["QRコード決済：R Pay（楽天ペイ）"], False)
        apply_yes_no(PaymentMethods.ALIPAY, item, location["QRコード決済：ALIPAY（支付宝）"], False)
        apply_yes_no(PaymentMethods.WECHAT, item, location["QRコード決済：WeChat Pay（微信支付）"], False)
        apply_yes_no(PaymentMethods.QUICPAY, item, location["電子マネー：QUICPay"], False)
        apply_yes_no(PaymentMethods.NANACO, item, location["電子マネー：nanaco"], False)
        apply_yes_no(PaymentMethods.WAON, item, location["電子マネー：WAON"], False)
        apply_yes_no(PaymentMethods.EDY, item, location["電子マネー：楽天Edy"], False)

        item["opening_hours"] = OpeningHours()
        day_ranges = {
            "平日営業時間": ["Mo", "Tu", "We", "Th", "Fr"],
            "土日祝営業時間": ["Sa", "Su"],
        }
        for range_name, days in day_ranges.items():
            if range_name not in location:
                continue
            if location[range_name] == "None" or not location[range_name]:
                continue
            for day in days:
                open_time = location[range_name].split("-")[0]
                close_time = location[range_name].split("-")[1]
                if len(open_time) == 4:  # HHMM should be HH:MM
                    open_time = open_time[:2] + ":" + open_time[:-2]
                elif len(open_time) != 5:  # HH:MM expected
                    break
                if len(close_time) == 4:  # HHMM should be HH:MM
                    close_time = close_time[:2] + ":" + close_time[:-2]
                elif len(close_time) != 5:  # HH:MM expected
                    break
                item["opening_hours"].add_range(day, open_time, close_time)

        yield item
