from locations.camoufox_spider import CamoufoxSpider
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
from locations.storefinders.manpower_partoo import ManpowerPartooSpider


class ManpowerFRSpider(ManpowerPartooSpider, CamoufoxSpider):
    name = "manpower_fr"
    sitemap_urls = ["https://vosagences.manpower.fr/sitemap.xml"]
    sitemap_rules = [(r"-\d+$", "parse_sd")]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//script[@type="application/ld+json"] | //*[local-name()="urlset"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]
