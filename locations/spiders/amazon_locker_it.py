from locations.spiders.amazon_locker import AmazonLockerSpider


class AmazonLockerITSpider(AmazonLockerSpider):
    name = "amazon_locker_it"
    allowed_domains = ["www.amazon.it"]
