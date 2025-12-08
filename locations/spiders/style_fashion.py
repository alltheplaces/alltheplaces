from locations.storefinders.amai_promap import AmaiPromapSpider


class StyleFashionSpider(AmaiPromapSpider):
    name = "style_fashion"
    start_urls = ["https://stylefashion.co.za/pages/store-locator-1"]
    item_attributes = {"brand": "Style", "brand_wikidata": "Q130350929"}

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        yield item
