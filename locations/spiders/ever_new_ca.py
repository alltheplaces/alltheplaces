from locations.spiders.forever_new_au_nz import FOREVER_NEW_SHARED_ATTRIBUTES, ForeverNewAUNZSpider


class EverNewCASpider(ForeverNewAUNZSpider):
    name = "ever_new_ca"
    item_attributes = FOREVER_NEW_SHARED_ATTRIBUTES
    start_urls = [
        "https://www.evernew.ca/locator/index/search/?longitude=0&latitude=0&radius=100000&type=all",
    ]
