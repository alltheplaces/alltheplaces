from locations.camoufox_spider import CamoufoxSpider
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS
from locations.spiders.eb_games_au import EbGamesAUSpider


class EbGamesNZSpider(EbGamesAUSpider, CamoufoxSpider):
    name = "eb_games_nz"
    sitemap_urls = ["https://www.ebgames.co.nz/sitemap-stores.xml"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS
