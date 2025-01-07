from locations.storefinders.woosmap import WoosmapSpider


class SmythstoysGBSpider(WoosmapSpider):
    name = "smythstoys_gb"
    item_attributes = {"brand": "SmythsToys", "brand_wikidata": "Q7546779"}
    key = "woos-49066dab-d11d-3614-98c7-ab241da1565b"
    origin = "https://www.smythstoys.com/"
