from locations.storefinders.woosmap import WoosmapSpider


class KiloutouFRSpider(WoosmapSpider):
    name = "kiloutou_fr"
    item_attributes = {"brand": "Kiloutou", "brand_wikidata": "Q3196672"}
    key = "woos-0bfdc0e9-2491-3363-bb8a-4ebf17f75be7"
    origin = "https://www.kiloutou.fr/"

    def parse_item(self, item, feature, **kwargs):
        item["branch"] = item.pop("name")
        item["website"] = f'https://www.kiloutou.fr{item["website"]}'

        yield item
