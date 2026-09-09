from locations.spiders.laser_clinics_au import LASER_CLINICS_SHARED_ATTRIBUTES, LaserClinicsSpider


class LaserClinicsGBSpider(LaserClinicsSpider):
    name = "laser_clinics_gb"
    item_attributes = {**LASER_CLINICS_SHARED_ATTRIBUTES, "country": "GB"}
    allowed_domains = ["www.laserclinics.co.uk"]
    sitemap_urls = ["https://www.laserclinics.co.uk/sitemap.xml"]
    requires_proxy = "GB"  # Vercel security checkpoint blocks datacentre IPs
