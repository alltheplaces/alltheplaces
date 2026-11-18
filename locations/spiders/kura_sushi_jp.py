import html
import json
import re
from collections.abc import Iterable

from scrapy import Request
from scrapy.http import TextResponse

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS_JP, OpeningHours
from locations.items import Feature
from locations.lang_utils import katakana_to_hiragana
from locations.structured_data_spider import StructuredDataSpider

# Some payment methods are in img alt text.
PAYMENT_METHODS = {
    "VISA": PaymentMethods.VISA,
    "Mastercard": PaymentMethods.MASTER_CARD,
    "JCB": PaymentMethods.JCB,
    "AmericanExpress": PaymentMethods.AMERICAN_EXPRESS,
    "DinersClubInternational": PaymentMethods.DINERS_CLUB,
    "Discover": PaymentMethods.DISCOVER_CARD,
    "RakutenCard": "payment:rakuten_card",
    "RPay": PaymentMethods.RAKUTEN_PAY,
    "LINEPay": PaymentMethods.LINE_PAY,
    "PayPay": PaymentMethods.PAYPAY,
    "d払い": PaymentMethods.D_BARAI,
    "Alipay": PaymentMethods.ALIPAY,
    "WeChatPay": PaymentMethods.WECHAT,
    "QUOPay": PaymentMethods.QUO_PAY,
    "AEONPay": PaymentMethods.AEON_PAY,
    "auPAY": PaymentMethods.AU_PAY,
    "FamiPay": PaymentMethods.FAMI_PAY,
    "ANAPay": "payment:ana_pay",
    "Merpay": PaymentMethods.MERPAY,
    "ララPay": "payment:lala_pay",
    "K+": "payment:k_plus",
    "Payどん": "payment:paydon",
    "ゆうちょPay": PaymentMethods.YUCHO_PAY,
    "銀行Pay": PaymentMethods.BANK_PAY,
    "EPOSPAY": "payment:epos_pay",
    "atone": "payment:atone",
    "pring": "payment:pring",
}
# Logos drawn on the image but missing from the alt text.
# Not tagged: GLN, wesmo!, N Pay, m Pay (no reliable payment:* key).
IMAGE_PAYMENT_METHODS = (
    PaymentMethods.UNIONPAY,
    PaymentMethods.SMART_CODE,
    "payment:gifteepremo_plus",
    "payment:jal_pay",
    "payment:myjcb_pay",
    "payment:mican_app",
    "payment:luvit_pay",
    "payment:bnpj_credit",
)

# 提供サービス boxes are rendered as box--active / box--inactive, so availability
# is explicit. Other boxes (brand apps, price tiers, store-format labels, LINE
# booking, daily promotions) have no standard OSM tag and are left unmapped.

# third-party delivery providers shown as service boxes:
# page label -> (trade name for delivery:partner, wikidata id)
# RocketNow has no wikidata item and is kept last.
DELIVERY_PARTNERS = {
    "Uber Eats": ("Uber Eats", "Q21462723"),
    "出前館": ("Demae-can", "Q11395551"),
    "RocketNow": ("Rocket Now", None),
}

# Stores marked closed or closed-for-renovation publish no hours and are dropped.
CLOSED_MARKERS = ("【閉店】", "【改装中】")


class KuraSushiJPSpider(StructuredDataSpider):
    name = "kura_sushi_jp"
    item_attributes = {"brand": "くら寿司", "brand_wikidata": "Q6445491"}
    allowed_domains = ["shop.kurasushi.co.jp"]
    wanted_types = ["LocalBusiness"]
    start_urls = ["https://shop.kurasushi.co.jp/all"]

    def parse(self, response: TextResponse, **kwargs) -> Iterable[Request]:
        for store_div in response.xpath('//div[@class="store"]'):
            if not (href := store_div.xpath('.//a[@class="sLink"]/@href').get()):
                continue
            if not (raw_data := store_div.xpath("./@data-store").get()):
                continue
            store = json.loads(html.unescape(raw_data))
            if any(marker in (store.get("name") or "") for marker in CLOSED_MARKERS):
                self.crawler.stats.inc_value(f"atp/{self.name}/store_closed")
                continue
            yield response.follow(href, callback=self.parse_sd, cb_kwargs={"store": store})

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        store = response.cb_kwargs.get("store") or {}

        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url

        # Avoid setting shop logo as POI image.
        item["image"] = None

        branch = (store.get("name") or "").split("【")[0].strip()
        if not branch:
            branch = (item.get("name") or "").removeprefix("くら寿司 ").strip()
        item["branch"] = branch
        item["name"] = None

        if kana := store.get("kana"):
            item["extras"]["branch:ja-Hira"] = katakana_to_hiragana(kana)

        if hours := self._parse_hours(response):
            item["opening_hours"] = hours

        if board := response.xpath('//img[@class="payment--pc"]'):
            for raw in (board.xpath("./@alt").get() or "").split("、"):
                if not (name := raw.strip()):
                    continue
                if method := PAYMENT_METHODS.get(name):
                    apply_yes_no(method, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unmapped_payment/{name}")
            for method in IMAGE_PAYMENT_METHODS:
                apply_yes_no(method, item, True)

        self._apply_services(item, response)
        self._apply_parking(item, response)
        self._apply_seats(item, response)

        apply_category(Categories.FAST_FOOD, item)

        yield item

    @staticmethod
    def _parse_hours(response: TextResponse) -> OpeningHours | None:
        oh = OpeningHours()
        for span in response.xpath('//div[contains(@class, "business-hour__detail")]/span'):
            text = re.sub(r"[\s　\xa0]+", " ", span.xpath("string(.)").get("")).strip()
            if not (m := re.match(r"([月火水木金土日](?:曜日)?)\s*(.*)$", text)):
                continue
            if (day := DAYS_JP.get(m.group(1))) is None:
                continue
            if times := re.match(r"(\d{1,2}:\d{2})\s*[-–〜~]\s*(\d{1,2}:\d{2})", m.group(2)):
                oh.add_range(day, times.group(1), times.group(2))
            elif "定休日" in m.group(2) or "休業" in m.group(2):
                oh.set_closed(day)
        # No public-holiday information is published, so PH is not added.

        return oh or None

    @staticmethod
    def _apply_services(item: Feature, response: TextResponse) -> None:
        services: dict[str, bool] = {}
        for box in response.xpath('//div[@class="service__list"]/div'):
            label = box.xpath("string(.//span)").get("").strip()
            classes = box.xpath("./@class").get("") or ""
            if label:
                services[label] = "box--active" in classes

        if services.get("多機能トイレ対応"):
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, True)
        if services.get("無料WIFI"):
            apply_yes_no(Extras.WIFI, item, True)
            item["extras"]["internet_access:fee"] = "no"
        if services.get("スロープ対応") or services.get("車いす用席対応"):
            apply_yes_no(Extras.WHEELCHAIR, item, True)
        if partners := [(name, qid) for label, (name, qid) in DELIVERY_PARTNERS.items() if services.get(label)]:
            apply_yes_no(Extras.DELIVERY, item, True)
            item["extras"]["delivery:partner"] = ";".join(name for name, _ in partners)
            if qids := [qid for _, qid in partners if qid]:
                item["extras"]["delivery:partner:wikidata"] = ";".join(qids)

    @staticmethod
    def _apply_parking(item: Feature, response: TextResponse) -> None:
        parking = response.xpath('//div[contains(@class, "parking__content")]')
        if not parking:
            return
        # なし is drawn as <svg aria-label="なし"> whose only text is a dash char.
        if parking.xpath('.//svg[@aria-label="なし"]'):
            apply_yes_no(Extras.PARKING, item, False, apply_positive_only=False)
        elif re.search(r"\d+", parking.xpath("string(.)").get("")):
            apply_yes_no(Extras.PARKING, item, True)

    @staticmethod
    def _apply_seats(item: Feature, response: TextResponse) -> None:
        seat = response.xpath('//div[contains(@class, "seat__content")]')
        if seat and (m := re.search(r"\d+", seat.xpath("string(.)").get(""))):
            item["extras"]["capacity"] = m.group(0)
