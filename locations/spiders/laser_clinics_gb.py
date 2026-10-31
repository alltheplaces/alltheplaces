from locations.spiders.laser_clinics_au import LASER_CLINICS_SHARED_ATTRIBUTES, LaserClinicsSpider


class LaserClinicsGBSpider(LaserClinicsSpider):
    name = "laser_clinics_gb"
    item_attributes = {**LASER_CLINICS_SHARED_ATTRIBUTES, "country": "GB"}
    allowed_domains = ["laserclinics.co.uk"]
    sitemap_urls = ["https://laserclinics.co.uk/sitemap.xml"]
    requires_proxy = "GB"
