from locations.storefinders.amazon_locker import AmazonLockerSpider


class AmazonLockerATCZDESpider(AmazonLockerSpider):
    # Countries removed for having no lockers: DK, EE, FI, FI, LT, LV
    name = "amazon_locker_at_cz_de"
    allowed_domains = ["www.amazon.de"]
