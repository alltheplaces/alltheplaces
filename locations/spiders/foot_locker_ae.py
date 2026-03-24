from locations.spiders.foot_locker_sa import FootLockerSASpider


class FootLockerAESpider(FootLockerSASpider):
    name = "foot_locker_ae"
    allowed_domains = ["www.footlocker.ae"]
    start_urls = [
        "https://www.footlocker.ae/rest/are_en/V1/storeLocator/search?searchCriteria%5Bfilter_groups%5D%5B0%5D%5Bfilters%5D%5B0%5D%5Bfield%5D=status&searchCriteria%5Bfilter_groups%5D%5B0%5D%5Bfilters%5D%5B0%5D%5Bvalue%5D=1"
    ]
