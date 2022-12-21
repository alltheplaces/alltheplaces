from locations.storefinders.woosmap import WoosmapSpider


class JardilandSpider(WoosmapSpider):
    name = "jardiland"
    item_attributes = {"brand": "Jardiland", "brand_wikidata": "Q3162276"}
    key = "jardiland-woos-staging"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Origin": "https://www.jardiland.com/"}}

    def parse_item(self, item, feature, **kwargs):
        item[
            "website"
        ] = f'https://www.jardiland.com/storelocator/store/view/name/{feature["properties"]["contact"]["website"]}/'
        yield item
