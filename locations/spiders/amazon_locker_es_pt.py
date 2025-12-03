from locations.storefinders.amazon_locker import AmazonLockerSpider


class AmazonLockerESPTSpider(AmazonLockerSpider):
    name = "amazon_locker_es_pt"
    allowed_domains = ["www.amazon.es"]
