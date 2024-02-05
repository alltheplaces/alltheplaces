from locations.categories import Categories
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class ScottishDentalCareGBSpider(AgileStoreLocatorSpider):
    name = "scottish_dental_care_gb"
    allowed_domains = ["scottishdentalcare.co.uk"]
    item_attributes = {"brand": "Scottish Dental Care", "extras": Categories.DENTIST.value}
