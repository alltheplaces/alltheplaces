from locations.spiders.laser_clinics_au import LASER_CLINICS_SHARED_ATTRIBUTES, LaserClinicsSpider


class LaserClinicsNZSpider(LaserClinicsSpider):
    name = "laser_clinics_nz"
    item_attributes = {**LASER_CLINICS_SHARED_ATTRIBUTES, "country": "NZ"}
    allowed_domains = ["www.laserclinicsnewzealand.co.nz"]
    sitemap_urls = ["https://www.laserclinicsnewzealand.co.nz/sitemap.xml"]
    requires_proxy = "NZ"  # Vercel security checkpoint blocks datacentre IPs
