import re
from urllib.parse import urlparse

import scrapy
from scrapy.commands import BaseRunSpiderCommand
from scrapy.exceptions import UsageError
from scrapy.spiders.sitemap import iterloc
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots

from locations.user_agents import BROWSER_DEFAULT


class MySitemapSpider(scrapy.spiders.SitemapSpider):
    name = "my_sitemap_spider"
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    pages = False
    download_delay = 0.5
    # Generated from the codebase, see https://github.com/alltheplaces/alltheplaces/issues/7723
    common_sitemap_patterns = [
        r"(.+)/marktseite$",
        r"-\d+$",
        r"-\d+\.html",
        r"-fast-food-restaurant-.+-\d+\/Map$",
        r"-id",
        r"-self-storage/$",
        r".*/us/en/.*/hoteldetail$",
        r".+/office-supplies-\w\w-\d+\.html",
        r".co.uk/restaurants/",
        r".co.uk/stores/([\d]+)-([\w-]+)",
        r"/(?:us|ca)/\w\w/[^/]+/[^/]+$",
        r"/([-\w]+)\/([-\w]+)\/([-\w]+)\/overview",
        r"/.+/.+/.+\.html",
        r"/[-\w]+/[-\w]+/[-\w]+",
        r"/[-\w]+\/[-.\w]+\/[-\/\w]+$",
        r"/[0-9]+",
        r"/[0-9]+/$",
        r"/[^/]+/[^/]+/[^/]+$",
        r"/[a-z0-9]{4,5}$",
        r"/\d+$",
        r"/\d+/$",
        r"/\d+/Oeffnungszeiten.html",
        r"/\w\w/[-\w]+/[-\w]+",
        r"/\w\w/[-\w]+/[-\w]+\.html",
        r"/\w\w/[^/]+/(\d+)$",
        r"/\w\w/[^/]+/(\d+)/$",
        r"/\w\w/[^/]+/[^/]+$",
        r"/\w\w/[^/]+/[^/]+(?<!-sc)\.html",
        r"/\w\w/[^/]+/[^/]+-(\d+)\.html",
        r"/\w\w/[^/]+/[^/]+.html",
        r"/\w\w/[^/]+/[^/]+/$",
        r"/\w\w/[^/]+/[^/]+/[^/]+$",
        r"/\w\w/[^/]+/[^/]+\.html",
        r"/\w\w/[^/]+/meal-prep-(\d+).html",
        r"/\w\w/[^/]+/shoe-store-.+-(\d+)\.html",
        r"/\w\w/\w+/[-\w]+\.html",
        r"/\w\w/\w\w/[^/]+/[^/]+\.html",
        r"/agencies/.",
        r"/agent/us/\w\w/[^/]+/[^/]+$",
        r"/anbieter\/(?!online-shop|kategorie)([-\w]+)\/[-\w]+$",
        r"/aruhazak/auchan-",
        r"/bakeries\/[^\/]+\/?$",
        r"/bakery-locator/",
        r"/bankomat/[\d]+",
        r"/batteries-plus-",
        r"/branch-",
        r"/branch-list/.+",
        r"/branch/",
        r"/branches/[-\w]+$",
        r"/branches\/([\w-]+\/[\w-]+)$",
        r"/bus-station-[0-9]+",
        r"/butiker/.+\d+/$",
        r"/car-hire\/[-\w]+\/[-\w]+\/[-\w]+\/$",
        r"/clothing-\d+\.html",
        r"/clubs/club.",
        r"/contact/$",
        r"/costcutter-*",
        r"/customer-service$",
        r"/de/.+/filialen/",
        r"/de/filialen/",
        r"/de/standorte/",
        r"/de/store/.+",
        r"/destinations\/([-\w]+)\/([-\w]+)\/$",
        r"/dialysis-centers/[-\w]+/\w+$",
        r"/discount-store-\d+.html",
        r"/drogerie/Drogeria-Rossmann-",
        r"/en-(?:\w\w/self-storage-[-\w]+|be/self-storage)/[-\w]+/[-\w]+$",
        r"/en-gb\/stores\/[-\w]+\/.+$",
        r"/en/find-us/.+",
        r"/facilities/",
        r"/fietsenwinkel/",
        r"/fietsenwinkel\/bike-totaal-[^/]+$",
        r"/filiale\/([\w]+)-([\w]+)-([\d]+)$",
        r"/find-a-car-park/car-parks/",
        r"/find-a-studio/.+/.+/$",
        r"/find-bhf-near-you/.+-bhf-shop",
        r"/find-station/.+-\d+$",
        r"/general-store/.*/[0-9]*",
        r"/geschaefte/",
        r"/getting-here$",
        r"/go-kart-tracks/",
        r"/gyms/",
        r"/happening\/stores\/(?!kohls).+",
        r"/hospital\/[\w\-]+\/$",
        r"/hotels/",
        r"/hotels\/[\w\-]+\/[\w\-]+$",
        r"/huts\/[-\w]+\/([-.\w]+)\/$",
        r"/kekes-",
        r"/local-bakery/",
        r"/local-tax-offices/.+/.+/.+/(\d+)/$",
        r"/locate-a-centre/",
        r"/location$",
        r"/location/",
        r"/location/big-boy",
        r"/location\/([\w\-]+)\/",
        r"/location\/[\w\-]+",
        r"/location\/\w\w\/[-\w]+\/[-\w&;]+$",
        r"/location\/\w{2}\/[\w\-]+\/$",
        r"/locations/",
        r"/locations/(?!$)",
        r"/locations/.+/.+$",
        r"/locations/[-\w]+",
        r"/locations/[-\w]+/[-\w]+/[-\w]+/[-\w]+/[-\w]+.html",
        r"/locations/[^/]+/[^/]",
        r"/locations/[^/]+/[^/]+/[^/]+$",
        r"/locations/\d+-[-\w]+/",
        r"/locations/propane-offices/[^/]+/[^/]+/[^/]+$",
        r"/locations/us/[-\w]+/[-\w]+/[0-9]+/$",
        r"/locations/veterinarians/\w\w/[-\w]+/\w\w\w$",
        r"/locations\/",
        r"/locations\/([-\w]+)$",
        r"/locations\/[^/]+/[^/]+$",
        r"/locations\/[^\/]+$",
        r"/locations\/[a-z]{2}\/[\w\-]+\/[\w\-]+\.html",
        r"/locations\/[a-z]{2}\/[\w\-]+\/[\w\-]+\/?$",
        r"/Locations\/States\/(\w{2})\/([-\w]+)\/(\d+)$",
        r"/lokacije/",
        r"/magasins/magasin-",
        r"/medias/sys_master/root/.*/Store-en-USD-.*.xml",
        r"/nationalsearch/\w+/[-\w]+$",
        r"/nl/winkel\/([\w]+)-([\w]+)-([\d]+)$",
        r"/o2-store-",
        r"/oddzial/[\d]+",
        r"/Office/Detail/",
        r"/offices/",
        r"/our-stores/",
        r"/outlet/[-\w]{2}/[-\w]{2}/[-\w]+/[-\w]+.html",
        r"/outlet/[^/]+/about$",
        r"/particulier/agence/[-\w]+/([-\w]+)\.html",
        r"/pharmacy$",
        r"/places/de/",
        r"/polska/.*[0-9]$",
        r"/practices/([-\w]+)$",
        r"/pubs\/([-\w]+)\/([-\w]+)$",
        r"/pubs\/([-\w]+)\/([-\w]+)\/$",
        r"/pubs\/([-\w]+)\/([-\w]+)\/?$",
        r"/pubs\/[\w\-]+\/[\w\-]+$",
        r"/real-estate-offices/",
        r"/restaurantes/",
        r"/restaurants-",
        r"/restaurants/",
        r"/restaurants/[-\w]+/[-\w]+$",
        r"/restaurants/[^/]+/[^/]+$",
        r"/restaurants\/[\w]+\/[\w]+$",
        r"/shop-finder\/([-\w]+)$",
        r"/shop/",
        r"/shops/",
        r"/shops/oxfam-",
        r"/sitemap_en-us_([\w]{2})_properties_\d\.xml",
        r"/standort/",
        r"/station-information/stations/",
        r"/station/circle-k-",
        r"/store",
        r"/store-\d",
        r"/store-\d+$",
        r"/store-\d+\.html",
        r"/store-directory\/\w{2}\/.*\/\d+$",
        r"/store-finder/",
        r"/store-finder\/[-\w]+$",
        r"/store-locations/.+/",
        r"/store-locator/",
        r"/store-locator/store/",
        r"/store-locator/store\.[\w%]+\.\d+\.html",
        r"/store/",
        r"/store\/(.+)$",
        r"/store\/(?!online)",
        r"/store\/(?:[^\/]+\/){2}s\d+$",
        r"/store\/(\d+)$",
        r"/store\/\w\w\/*\/*\/",
        r"/storefinder/store/.+-(\d+)$",
        r"/stores/",
        r"/stores/.*/.*",
        r"/stores/.+/.+/\w+\d+$",
        r"/stores/[-\w]+",
        r"/stores/[-\w]+$",
        r"/stores/[-\w]+/[-\w]+/$",
        r"/stores/[-\w]+/[-\w]+/[-\w]+.html",
        r"/stores/[^/]+$",
        r"/stores/[^/]+\/$",
        r"/stores/[^\\]+\-\w\w\-(\d+)$",
        r"/stores/\w\w/\w+/gap-(\d+)\.html",
        r"/stores/\w\w/\w\w/[-\w]+/[-\w]+$",
        r"/stores/store/(\d+)-[-\w]+$",
        r"/stores\/(?:act|nsw|nt|qld|sa|tas|vic|wa)\/[\w\-]+$",
        r"/warehouse-locations/[^.]+-(\d+)\.html",
        r"/winkels/",
        r"[0-9]+$",
        r"[0-9]+.html",
        r"\.com/\w\w/[-.\w]+/[-.\w]+$",
        r"\.com/\w\w/[^/]+/[^/]+$",
        r"\.com/\w\w/[^/]+/clothing-store-(\d+)\.html",
        r"\.com\/([-\w]{3,})$",
        r"\.coop\/[-\w]+\/[-\w]+\/[-\w]+\.html",
        r"\/stores\/",
        r"\/stores\/([-.\w]+)$",
        r"\/stores\/([-\w]+)\.html",
        r"\/Stores\/[-._\w]+-(\d+)$",
        r"\/stores\/[\w\-]+\/$",
        r"\/stores\/\w{2}\/\w+-(\d+)\.shtml",
        r"\/stores\/details\?sid=(?:bcf|rebel|sca)-[\w\-]+$",
        r"\/uk\/store\/[-\w]+-(\d+)$",
        r"\/vapestore-([-\w]+)",
        r"\/winkel\/([\w]+)-([\w]+)-([\d]+)$",
        r"\d+\.html",
        r"_POS$",
        r"baumarkt",
        r"boutiques\.(.*)/.*/.*/.*/results$",
        r"branch-locations/.",
        r"en_US/book/.*\.html",
        r"find-a-showroom/(.*)",
        r"fr/[^/]+/[^/]+/[^/]+$",
        r"https://branches.(.*)/.+/.+/.+",
        r"https://branches\.(.*)[-\w]+\/[-\/'\w]+$",
        r"https://branches\.(.*)\.co\.uk\/[-'\w]+\/[-'\/\w]+$",
        r"https://branches\.(.*)\.co\.uk\/[-\w]+\/[-\/\w]+\.html",
        r"https://branches\.(.*)\.co\.uk\/[\w\-]+\/[\w\-]+\.html",
        r"https://burgerurge\.com\.au\/location\/[\w\-]+\/$",
        r"https://filialen\.(.*)",
        r"https://local\.(.*)/[^/]+/[^/]+/[^/]+$",
        r"\w\w/[-\w]+/[-\w]+\.html",
        r"https://locations(.*).com/[-\w]+/[-\w]+/[-\w]+",
        r"https://locations(.*)/.*/.*/.*",
        r"https://locations(.*)/.+/.+/.+",
        r"https://locations(.*)/.+/.+/.+/.+.html",
        r"https://locations(.*)/.+/\w\w/.+/.+",
        r"https://locations(.*)/.+\/.+\/.+\/.+",
        r"https://locations(.*)/[^/]+/[^/]+/[^/]+$",
        r"https://locations(.*)/[^/]+/[^/]+/[^/]+.html",
        r"https://locations(.*)/[^e].+\/.+\/.+\/.+",
        r"https://locations(.*)/\w\w/.+/.+\.html",
        r"https://locations(.*)/\w\w/[-'\w]+/[-.'()\w]+$",
        r"https://locations(.*)/\w\w/[-.\w]+/[-–\w]+$",
        r"https://locations(.*)/\w\w/[-\w]+/[-\w]+\.html",
        r"https://locations(.*)\/\w\w\/[-.\w]+$",
        r"https://locations(.*)\/\w{2}\/[-\w]+$",
        r"https://locator(.*)\/(?!es)[a-z]{2}\/[\w\-]+\/[\w\-]+$",
        r"https://restaurants(.*)/(?!(index\.html|search$))[^/]+$",
        r"https://restaurants(.*)/[^/]+$",
        r"https://restaurants(.*)/en-us/\w\w/[-\w]+/[-.\w]+\d+$",
        r"https://restaurants(.*)/en_kw\/[^/]+$",
        r"https://restaurants(.*)\.hk\/en_hk\/(?!search$)[^/]+$",
        r"https://restaurants(.*)\.kr\/en\/(?!search$)[^/]+$",
        r"https://restaurants(.*)\/[^/]+$",
        r"https://restaurants(.*)\/en\/(?!search$)[^/]+$",
        r"https://restaurants(.*)\/en\/[^/]+$",
        r"https://restaurants(.*)\/en_ae\/[^/]+$",
        r"https://restaurants(.*)\/en_at\/(?!search$)[^/]+$",
        r"https://restaurants(.*)\/en_be\/[^/]+$",
        r"https://restaurants(.*)\/en_bh\/(?!search$)[^/]+$",
        r"https://restaurants(.*)\/en_ch\/[^/]+$",
        r"https://restaurants(.*)\/en_it\/[^/]+$",
        r"https://restaurants(.*)\/en_lu\/[^/]+$",
        r"https://restaurants(.*)\/en_nl\/[^/]+$",
        r"https://restaurants(.*)\/en_qa\/[^/]+$",
        r"https://restaurants(.*)\/en_sa\/[^/]+$",
        r"https://store-locations\.(.*)/.*/.*/.*/",
        r"https://store\.(.*)/\w+\/[-\w]+\/[-\w]+",
        r"https://store\.(.*)\/[-.\w]+\/[-.\w]+$",
        r"https://stores(.*)/[-\w]+/[-\w]+/\d+/$",
        r"https://stores(.*)/[^/]+/[^/]+/[^/]+$",
        r"https://stores.(.*)/.+/.+/.+/.+.html",
        r"https://stores.(.*)/[-\w]+",
        r"https://stores.(.*)/[^/]*/[^/]*/[^/]*$",
        r"https://stores.(.*)/all-stores-[^/]+/[^/]+/[^/]+$",
        r"https://stores.(.*)\/[^/]+/[^/]+/[^/]+.html",
        r"https://stores\.(.*)-bateau\.com\/[a-z\-]{3,}\/.+",
        r"https://stores\.(.*)\.com/.*/.*/.*/$",
        r"https://stores\.(.*)\.com/.*/.*/$",
        r"https://stores\.(.*)\.com/\w\w/[-\w]+/[-\w]+\.html",
        r"https://stores\.(.*)\.com/\w\w/\w\w/[-.\w]+/[-.'\w]+$",
        r"https://stores\.(.*)\.com\/(?!es\/)[^/]+/[^/]+/[^/]+$",
        r"https://stores\.(.*)\.com\/[-\w]+\/[-\w]+\/[-\w%']+",
        r"https://stores\.(.*)\.com\/[a-z]{2}-[a-z]{2}\/[a-z]{2}(?:\/[-\w]+){3}$",
        r"https://stores\.(.*)\.coop\/[-\w]+\/.*$",
        r"https://stores\.(.*)\.net\/[^(?{2,})]+-([\w\d]+)\.html",
        r"https://stores\.(.*)\.us/.*/.*/.*$",
        r"https://tiendas.(.*).es\/tiendas\/.+\/.+\/.+",
        r"it/[^/]+/\w\w/.+$",
        r"location\/.*\/$",
        r"locations/(.*)$",
        r"locations/.*/.*/.*/.*",
        r"locations\.(.*)(?:\/[a-z]{2}){1,2}(?:\/[\w\-.]{3,}){2}",
        r"locations\.(.*)/.*/.*/.*$",
        r"locations\.(.*)\/en\/[a-z]{2}\/[\w\-]+\/[\w\-]+\/\d+$",
        r"magasins\.(.*)/.*/.*/.*/results$",
        r"nasze-sklepy\/[a-zA-Z0-9-]+\.html",
        r"palmbeachtan.com/locations/[A-Z]{2}/\w+",
        r"pet-supplies-(.+).html",
        r"pizzeria-.*",
        r"retail-stores/",
        r"\/store\/\d+$",
        r"stores/[^/]+/[^/]+/[^/]+$",
        r"stores\.(.*)/\d+$",
        r"stores\.(.*)/fl/\w+/$",
        r"stores\.(.*)\/\w-\-.*$",
    ]
    matched_patterns = {}

    # Examine a url and highlight possible store pages, store finder pages of interest
    def extract_possible_store(self, url):
        print(url)
        for pattern in self.common_sitemap_patterns:
            if re.search(pattern, url):
                if pattern in self.matched_patterns:
                    self.matched_patterns[pattern] = self.matched_patterns[pattern] + 1
                else:
                    self.matched_patterns[pattern] = 1

    def _parse_sitemap(self, response):
        if response.url.endswith("/robots.txt"):
            for url in sitemap_urls_from_robots(response.text, base_url=response.url):
                if not self.pages:
                    print(url)
                yield scrapy.Request(url, callback=self._parse_sitemap)
        else:
            body = self._get_sitemap_body(response)
            if body is None:
                print("invalid sitemap response: " + response.url)
                return

            s = Sitemap(body)
            it = self.sitemap_filter(s)

            if s.type == "sitemapindex":
                for loc in iterloc(it, self.sitemap_alternate_links):
                    if any(x.search(loc) for x in self._follow):
                        if not self.pages:
                            print(loc)
                        yield scrapy.Request(loc, callback=self._parse_sitemap)
            elif s.type == "urlset":
                for loc in iterloc(it, self.sitemap_alternate_links):
                    if self.pages:
                        self.extract_possible_store(loc)

                if len(self.matched_patterns) > 0:
                    print("Possible patterns")
                    print(self.matched_patterns)


class SitemapCommand(BaseRunSpiderCommand):
    requires_project = True
    default_settings = {"LOG_ENABLED": False}

    def syntax(self):
        return "[options] <root URL | robots.txt URL | sitemap URL>"

    def short_desc(self):
        return "Probe website robots.txt / sitemap.xml for spider development insights"

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--pages",
            action="store_true",
            help="print HTTP page links rather than sitemap XML links, helps identify POI pages",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="show crawler stats",
        )

    def run(self, args, opts):
        if len(args) != 1:
            raise UsageError("Please specify a URL for the SitemapSpider")

        url = args[0]
        parsed = urlparse(url)
        if parsed.path.replace("/", "") == "":
            # If URL has no path data then take a chance on robots.txt being there to help.
            url = parsed.scheme + "://" + parsed.netloc + "/robots.txt"
        MySitemapSpider.sitemap_urls = [url]

        MySitemapSpider.pages = opts.pages

        crawler = self.crawler_process.create_crawler(MySitemapSpider, **opts.spargs)
        self.crawler_process.crawl(crawler)
        self.crawler_process.start()
        if opts.stats:
            for k, v in crawler.stats.get_stats().items():
                print(k + ": " + str(v))
