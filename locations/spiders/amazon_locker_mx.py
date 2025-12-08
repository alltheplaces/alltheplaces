from locations.storefinders.amazon_locker import AmazonLockerSpider


class AmazonLockerMXSpider(AmazonLockerSpider):
    name = "amazon_locker_mx"
    allowed_domains = ["www.amazon.com.mx"]
