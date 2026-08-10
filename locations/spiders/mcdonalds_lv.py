from locations.storefinders.mcdonalds_premier_capital import McdonaldsPremierCapitalSpider


class McdonaldsLVSpider(McdonaldsPremierCapitalSpider):
    name = "mcdonalds_lv"
    domain = "mcdonalds.lv"
    start_urls = ["https://mcdonalds.lv/atrodi/"]
