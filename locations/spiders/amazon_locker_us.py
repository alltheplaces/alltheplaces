from locations.storefinders.amazon_locker import AmazonLockerSpider


class AmazonLockerUSSpider(AmazonLockerSpider):
    # Countries removed for having no lockers: IL
    name = "amazon_locker_us"
    allowed_domains = ["www.amazon.com"]
