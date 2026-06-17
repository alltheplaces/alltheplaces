from locations.spiders.petstock_au import PetstockAUSpider


class PetstockNZSpider(PetstockAUSpider):
    name = "petstock_nz"
    api_key = "c545abd23934d9a1a200961d8d189708"
    app_id = "HX85NPQ0XP"
    domain = "co.nz"
