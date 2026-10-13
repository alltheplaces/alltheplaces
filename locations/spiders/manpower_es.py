from locations.storefinders.manpower_partoo import ManpowerPartooSpider


class ManpowerESSpider(ManpowerPartooSpider):
    name = "manpower_es"
    sitemap_urls = ["https://oficinas.manpower.es/sitemap.xml"]
