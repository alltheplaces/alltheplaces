from locations.storefinders.storeify import StoreifySpider


class TheBodyShopGBSpider(StoreifySpider):
    name = "the_body_shop_gb"
    item_attributes = {"brand": "The Body Shop", "brand_wikidata": "Q837851"}
    api_key = "the-body-shop-uk.myshopify.com"
    domain = "https://www.thebodyshop.com/"
