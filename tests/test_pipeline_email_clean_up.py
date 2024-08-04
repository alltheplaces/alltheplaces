from scrapy import Spider
from scrapy.utils.test import get_crawler

from locations.items import Feature
from locations.pipelines.email_clean_up import EmailCleanUpPipeline


def get_objects(email):
    spider = Spider(name="test")
    spider.crawler = get_crawler()
    return (
        Feature(email=email),
        EmailCleanUpPipeline(),
        spider,
    )


def test_handle_valid():
    # Valid examples https://en.wikipedia.org/wiki/Email_address

    valid = [
        "simple@example.com",
        "very.common@example.com",
        "FirstName.LastName@EasierReading.org",
        "x@example.com",
        "long.email-address-with-hyphens@and.subdomains.example.com",
        "user.name+tag+sorting@example.com",
        "name/surname@example.com",
        "admin@example",
        "example@s.example",
        '" "@example.org',
        '"john..doe"@example.org',
        "mailhost!username@example.org",
        '"very.(),:;<>[]".VERY."very@\\ "very".unusual"@strange.example.com',
        "user%example.com@example.org",
        "user-@example.org",
        "postmaster@[123.123.123.123]",
        "postmaster@[IPv6:2001:0db8:85a3:0000:0000:8a2e:0370:7334]",
        "_test@[IPv6:2001:0db8:85a3:0000:0000:8a2e:0370:7334]",
    ]

    for email in valid:
        item, pipeline, spider = get_objects(email)
        pipeline.process_item(item, spider)
        assert item.get("email") == email


def test_handle_invalid():
    invalid = [
        "abc.example.com",
        # Further examples to be added with an appropriate RFC based email validator like https://pypi.org/project/email-validator/
        # "a@b@c@example.com",
        # 'a"b(c)d,e:f;g<h>i[j\k]l@example.com',
        # 'just"not"right@example.com',
        # 'this is"not\allowed@example.com',
        # 'this\ still"not\\allowed@example.com',
        # "1234567890123456789012345678901234567890123456789012345678901234+x@example.com",
        # "i.like.underscores@but_they_are_not_allowed_in_this_part",
    ]

    for email in invalid:
        item, pipeline, spider = get_objects(email)
        pipeline.process_item(item, spider)
        assert item.get("email") is None
