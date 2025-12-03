from locations.spiders.amazon_locker import AmazonLockerSpider


class AmazonLockerAUSpider(AmazonLockerSpider):
    name = "amazon_locker_au"
    allowed_domains = ["www.amazon.com.au"]
