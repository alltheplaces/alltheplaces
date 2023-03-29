from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class MephistoBESpider(AmastyStoreLocatorSpider):
    name = "mephisto_be"
    item_attributes = {"brand": "Mephisto", "brand_wikidata": "Q822975"}
    allowed_domains = ["www.mephisto.com/be-fr"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_item(self, item, location, popup_html):
        # We don't want resellers. Only brand shop.
        if item["name"] == "MEPHISTO-SHOP":
            yield item
