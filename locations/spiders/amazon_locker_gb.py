from locations.storefinders.amazon_locker import AmazonLockerSpider


class AmazonLockerGBSpider(AmazonLockerSpider):
    name = "amazon_locker_gb"
    allowed_domains = ["www.amazon.co.uk"]
