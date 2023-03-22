from locations.storefinders.storerocket import StoreRocketSpider


class NickTheGreekUSSpider(StoreRocketSpider):
    name = "nick_the_greek_us"
    item_attributes = {"brand": "Nick The Greek", "brand_wikidata": "Q117222612"}
    storerocket_id = "DMJbVkRJXe"
    base_url = "https://www.nickthegreek.com/"

    def parse_item(self, item, location):
        # slug and url returned are incorrect and seemingly there
        # is no other way to recover the website URL.
        item.pop("website")

        # remove unused/non-store-specific-value fields
        if item["email"] == "office@nickthegreek.com":
            item.pop("email")
        item.pop("facebook")
        item.pop("twitter")
        item["extras"].pop("instagram")

        yield item
