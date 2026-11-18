from locations.storefinders.manpower_partoo import ManpowerPartooSpider


class ManpowerDESpider(ManpowerPartooSpider):
    name = "manpower_de"
    sitemap_urls = ["https://www.standorte.manpower.de/sitemap.xml"]
