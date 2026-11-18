from locations.storefinders.manpower_partoo import ManpowerPartooSpider


class ManpowerGBSpider(ManpowerPartooSpider):
    name = "manpower_gb"
    sitemap_urls = ["https://locations.manpower.co.uk/sitemap.xml"]
