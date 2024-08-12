from locations.storefinders.momentfeed import MomentFeedSpider


class CoffeeTimeSpider(MomentFeedSpider):
    name = "coffee_time"
    item_attributes = {"brand": "Coffee Time", "brand_wikidata": "Q5140932"}
    id = "YDGUJSNDOUAFKPRL"

    def parse_item(self, item, feature, store_info, **kwargs):
        item["website"] = f'https://locations.coffeetime.com{feature["llp_url"]}'
        yield item
