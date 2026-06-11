from locations.storefinders.mcdonalds_premier_capital import McdonaldsPremierCapitalSpider


class McdonaldsMTSpider(McdonaldsPremierCapitalSpider):
    name = "mcdonalds_mt"
    domain = "mcdonalds.com.mt"
    start_urls = ["https://mcdonalds.com.mt/locate/"]
