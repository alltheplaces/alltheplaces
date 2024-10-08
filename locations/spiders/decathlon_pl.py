from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonPLSpider(DecathlonFRSpider):
    name = "decathlon_pl"
    key = "woos-1a635f2d-aee1-3a1d-a21e-a8fe3ae1da21"
    origin = "https://www.decathlon.pl"
    website_template = "https://www.decathlon.pl/store-view/sport-shop-{slug}-{ref}"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name", None)
        yield item
