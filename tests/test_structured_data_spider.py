from scrapy import Selector
from scrapy.utils.test import get_crawler

from locations.categories import PaymentMethods
from locations.items import Feature
from locations.spiders.albertsons import AlbertsonsSpider
from locations.structured_data_spider import clean_twitter, extract_twitter


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
    assert item["extras"][PaymentMethods.CHEQUE.value] == "yes"
    assert item["extras"][PaymentMethods.DISCOVER_CARD.value] == "yes"
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


def test_clean_twitter_url():
    assert clean_twitter("https://twitter.com/exampleuser") == "exampleuser"
    assert clean_twitter("https://www.twitter.com/exampleuser") == "exampleuser"
    assert clean_twitter("http://twitter.com/exampleuser") == "exampleuser"
    assert clean_twitter("https://twitter.co.uk/exampleuser") == "exampleuser"


def test_clean_twitter_x_url():
    assert clean_twitter("https://x.com/exampleuser") == "exampleuser"
    assert clean_twitter("https://www.x.com/exampleuser") == "exampleuser"
    assert clean_twitter("http://x.com/exampleuser") == "exampleuser"


def test_clean_twitter_handle():
    assert clean_twitter("@exampleuser") == "exampleuser"
    assert clean_twitter("exampleuser") == "exampleuser"


def test_clean_twitter_strips_query_params():
    assert clean_twitter("https://twitter.com/exampleuser?ref=website") == "exampleuser"
    assert clean_twitter("https://x.com/exampleuser?ref=website") == "exampleuser"


def test_extract_twitter_from_meta():
    item = Feature()
    selector = Selector(text='<html><head><meta name="twitter:site" content="@exampleuser"></head></html>')
    extract_twitter(item, selector)
    assert item["twitter"] == "exampleuser"


def test_extract_twitter_from_twitter_link():
    item = Feature()
    selector = Selector(text='<html><body><a href="https://twitter.com/exampleuser">Twitter</a></body></html>')
    extract_twitter(item, selector)
    assert item["twitter"] == "exampleuser"


def test_extract_twitter_from_x_link():
    item = Feature()
    selector = Selector(text='<html><body><a href="https://x.com/exampleuser">X</a></body></html>')
    extract_twitter(item, selector)
    assert item["twitter"] == "exampleuser"


def test_extract_twitter_meta_takes_precedence():
    item = Feature()
    selector = Selector(
        text='<html><head><meta name="twitter:site" content="@metauser"></head>'
        '<body><a href="https://twitter.com/linkuser">Twitter</a></body></html>'
    )
    extract_twitter(item, selector)
    assert item["twitter"] == "metauser"


def test_extract_twitter_no_twitter():
    item = Feature()
    selector = Selector(text='<html><body><a href="https://netflix.com/movie">No social links</a></body></html>')
    extract_twitter(item, selector)
    assert item.get("twitter") is None
