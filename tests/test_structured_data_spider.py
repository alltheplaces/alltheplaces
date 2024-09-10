from scrapy.utils.test import get_crawler

from locations.categories import PaymentMethods
from locations.items import Feature
from locations.spiders.albertsons import AlbertsonsSpider


def get_objects():
    spider = AlbertsonsSpider()
    spider.crawler = get_crawler()
    return Feature(), spider


def test_payments_list():
    item, spider = get_objects()
    spider.extract_payment_accepted(
        item,
        None,
        {
            "paymentAccepted": [
                "American Express",
                "Google Pay",
                "Apple Pay",
                "Cash",
                "Check",
                "Discover",
                "MasterCard",
                "Samsung Pay",
                "Visa",
            ]
        },
    )
    assert item["extras"][PaymentMethods.AMERICAN_EXPRESS.value] == "yes"
    assert item["extras"][PaymentMethods.GOOGLE_PAY.value] == "yes"
    assert item["extras"][PaymentMethods.APPLE_PAY.value] == "yes"
    assert item["extras"][PaymentMethods.CASH.value] == "yes"
    # assert item["extras"][PaymentMethods.CHEQUE.value] == "yes"
    # assert item["extras"][PaymentMethods.DISCOVER_CARD.value] == "yes"
    assert item["extras"][PaymentMethods.MASTER_CARD.value] == "yes"
    assert item["extras"][PaymentMethods.SAMSUNG_PAY.value] == "yes"
    assert item["extras"][PaymentMethods.VISA.value] == "yes"


def test_payments_string():
    item, spider = get_objects()
    spider.extract_payment_accepted(
        item,
        None,
        {"paymentAccepted": "Cash, Credit Card, Debit Card"},
    )
    assert item["extras"][PaymentMethods.CASH.value] == "yes"
    assert item["extras"][PaymentMethods.CREDIT_CARDS.value] == "yes"
    assert item["extras"][PaymentMethods.DEBIT_CARDS.value] == "yes"


def test_payments_messy_string():
    item, spider = get_objects()
    spider.extract_payment_accepted(
        item,
        None,
        {"paymentAccepted": "cash,credit cards,             debit card"},
    )
    assert item["extras"][PaymentMethods.CASH.value] == "yes"
    assert item["extras"][PaymentMethods.CREDIT_CARDS.value] == "yes"
    assert item["extras"][PaymentMethods.DEBIT_CARDS.value] == "yes"
