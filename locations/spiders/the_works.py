from locations.storefinders.woosmap import WoosmapSpider


class TheWorksSpider(WoosmapSpider):
    name = "the_works"
    item_attributes = {"brand": "The Works", "brand_wikidata": "Q7775853"}
    key = "woos-c51a7170-fe29-3221-a27e-f73187126d1b"
    origin = "https://www.theworks.co.uk"

    def parse_item(self, item, feature, **kwargs):
        item["branch"] = item.pop("name")
        item["website"] = f'https://www.theworks.co.uk/Store?storeId={item["ref"]}'

        yield item
