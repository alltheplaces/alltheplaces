from locations.spiders.maxi_zoo_fr import MaxiZooFRSpider


class MaxiZooPLSpider(MaxiZooFRSpider):
    name = "maxi_zoo_pl"
    api_key = "maxizooPL"
    website_format = "https://www.maxizoo.pl/stores/{}/"
