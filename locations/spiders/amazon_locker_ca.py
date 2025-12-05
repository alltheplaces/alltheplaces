from locations.storefinders.amazon_locker import AmazonLockerSpider


class AmazonLockerCASpider(AmazonLockerSpider):
    name = "amazon_locker_ca"
    allowed_domains = ["www.amazon.ca"]
