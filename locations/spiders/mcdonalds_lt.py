from locations.storefinders.mcdonalds_premier_capital import McdonaldsPremierCapitalSpider


class McdonaldsLTSpider(McdonaldsPremierCapitalSpider):
    name = "mcdonalds_lt"
    domain = "mcd.lt"
    start_urls = ["https://mcd.lt/locate/"]
