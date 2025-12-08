from locations.spiders.maxi_zoo_fr import MaxiZooFRSpider


class MaxiZooIESpider(MaxiZooFRSpider):
    name = "maxi_zoo_ie"
    api_key = "maxizooIE"
    website_format = "https://www.maxizoo.ie/stores/{}/"
