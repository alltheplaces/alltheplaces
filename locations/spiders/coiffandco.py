from locations.spiders.jean_louis_david import JeanLouisDavidSpider


class CoiffandcoSpider(JeanLouisDavidSpider):
    name = "coiffandco"
    item_attributes = {"brand": "Coiff&Co", "brand_wikidata": "Q115013410"}
    sitemap_urls = ["https://www.coiffandco.com/sitemaps/sitemap-hairdressers.xml"]
