from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider


class NorthCarolinaDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "north_carolina_department_of_transportation_us"
    item_attributes = {
        "operator": "North Carolina Department of Transportation",
        "operator_wikidata": "Q3438398",
        "state": "NC",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["eapps.ncdot.gov"]
    start_urls = ["https://eapps.ncdot.gov/services/traffic-prod/v1/cameras/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Invalid robots.txt redirect off-site
