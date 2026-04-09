from locations.storefinders.amazon_locker import AmazonLockerSpider


class AmazonLockerNLSpider(AmazonLockerSpider):
    name = "amazon_locker_nl"
    allowed_domains = ["www.amazon.nl"]
