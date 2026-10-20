from locations.spiders.laser_clinics_au import LASER_CLINICS_SHARED_ATTRIBUTES, LaserClinicsSpider


class LaserClinicsCASpider(LaserClinicsSpider):
    name = "laser_clinics_ca"
    item_attributes = {**LASER_CLINICS_SHARED_ATTRIBUTES, "country": "CA"}
    allowed_domains = ["www.laserclinics.ca"]
    sitemap_urls = ["https://www.laserclinics.ca/sitemap.xml"]
    requires_proxy = "CA"  # Vercel security checkpoint blocks datacentre IPs
