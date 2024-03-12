from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ProperJobGBSpider(WPStoreLocatorSpider):
    name = "proper_job_gb"
    item_attributes = {
        "brand_wikidata": "Q83741810",
        "brand": "Proper Job",
    }
    allowed_domains = [
        "www.properjob.biz",
    ]
    time_format = "%I:%M %p"
