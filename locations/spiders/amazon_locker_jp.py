from locations.storefinders.amazon_locker import AmazonLockerSpider


class AmazonLockerJPSpider(AmazonLockerSpider):
    name = "amazon_locker_jp"
    allowed_domains = ["www.amazon.co.jp"]
