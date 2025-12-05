from locations.storefinders.amazon_locker import AmazonLockerSpider


class AmazonLockerFRSpider(AmazonLockerSpider):
    # Countries removed for having no lockers: LU, MC
    name = "amazon_locker_fr"
    allowed_domains = ["www.amazon.fr"]
