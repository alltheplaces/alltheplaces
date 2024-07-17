from locations.storefinders.storerocket import StoreRocketSpider


class NickTheGreekUSSpider(StoreRocketSpider):
    name = "nick_the_greek_us"
    item_attributes = {"brand": "Nick The Greek", "brand_wikidata": "Q117222612"}
    storerocket_id = "DMJbVkRJXe"
    base_url = "https://www.nickthegreek.com/"

    def parse_item(self, item, location):
        item["website"] = "https://www.nickthegreek.com/locations"
        # remove unused/non-store-specific-value fields
        if item["email"] == "office@nickthegreek.com":
            item.pop("email")
        item.pop("facebook")
        item.pop("twitter")
        item["extras"].pop("contact:instagram")
        yield item
