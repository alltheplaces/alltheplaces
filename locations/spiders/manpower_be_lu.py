from locations.storefinders.manpower_partoo import ManpowerPartooSpider


class ManpowerBELUSpider(ManpowerPartooSpider):
    name = "manpower_be_lu"
    sitemap_urls = ["https://interim-branches.manpower.be/sitemap.xml"]
