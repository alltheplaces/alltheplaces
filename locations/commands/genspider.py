import argparse
import os
import shutil
from importlib import import_module
from pathlib import Path
from typing import Union

import scrapy.commands.genspider
from scrapy.commands.genspider import extract_domain, render_templatefile, string_camelcase

from locations.name_suggestion_index import NSI


class Command(scrapy.commands.genspider.Command):
    # TODO: Remove this when autospidergen is merged
    parameters: dict = {
        "brand": None,
        "brand_wikidata": None,
        "operator": None,
        "operator_wikidata": None,
    }

    def add_options(self, parser: argparse.ArgumentParser) -> None:
        super().add_options(parser)
        parser.add_argument(
            "--brand-wikidata",
            dest="brand_wikidata",
            help="attempt to pre-fill brand name and NSI category based on supplied Wikidata Q-code",
        )
        parser.add_argument(
            "--operator-wikidata",
            dest="operator_wikidata",
            help="attempt to pre-fill operator name and NSI category based on supplied Wikidata Q-code",
        )

    # TODO: Remove this when autospidergen is merged
    def automatically_set_brand_or_operator_from_start_url(self):
        """
        Automatically extract parameters["brand_wikidata"] or
        parameters["operator_wikidata"] from a supplied
        start_urls[0]. Name Suggestion Index data is searched to find
        an entry that has the same domain name as start_urls[0]. If
        a match is found, parameters["brand_wikidata"] or
        parameters["operator_wikidata"] are automatically set.
        """
        if not self.parameters["brand_wikidata"] and not self.parameters["operator_wikidata"] and self.start_urls:
            nsi = NSI()
            wikidata_code = nsi.get_wikidata_code_from_url(self.start_urls[0])
            if wikidata_code:
                nsi_matches = [nsi_match for nsi_match in nsi.iter_nsi(wikidata_code)]
                if len(nsi_matches) == 1:
                    if "brand:wikidata" in nsi_matches[0]["tags"].keys():
                        self.parameters["brand_wikidata"] = wikidata_code
                    elif "operator:wikidata" in nsi_matches[0]["tags"].keys():
                        self.parameters["operator_wikidata"] = wikidata_code

    # TODO: Remove this when autospidergen is merged
    def automatically_set_parameters(self):
        """
        Automatically extract parameters from at least one or more
        of the following:
          1. start_urls[0]
          2. parameters["brand_wikidata"]
          3. parameters["operator_wikidata"]

        If any of the above are specified for this spider, and this
        method is called, this method will attempt to populate all
        other parameters automatically from Name Suggestion Index
        data.

        See automatically_set_brand_or_operator_from_start_url(self)
        for details on how parameters are extracted from just a single
        supplied start_urls[0].
        """
        if not self.parameters["brand_wikidata"] and not self.parameters["operator_wikidata"]:
            self.automatically_set_brand_or_operator_from_start_url()

        nsi = NSI()
        if self.parameters["brand_wikidata"] or self.parameters["operator_wikidata"]:
            wikidata_code = self.parameters["brand_wikidata"] or self.parameters["operator_wikidata"]
            nsi_matches = [nsi_match for nsi_match in nsi.iter_nsi(wikidata_code)]
            if len(nsi_matches) != 1:
                return

            if found_keys := NSI.generate_keys_from_nsi_attributes(nsi_matches[0]):
                self.parameters["spider_key"] = found_keys[0]
                self.parameters["spider_class_name"] = found_keys[1]

            if self.parameters["brand_wikidata"]:
                brand = nsi_matches[0]["tags"].get("brand", nsi_matches[0]["tags"].get("name"))
                self.parameters["brand"] = brand
            elif self.parameters["operator_wikidata"]:
                operator = nsi_matches[0]["tags"].get("operator", nsi_matches[0]["tags"].get("name"))
                self.parameters["operator"] = operator

    def _generate_template_variables(
        self,
        module: str,
        name: str,
        url: str,
        template_name: str,
    ):
        capitalized_module = "".join(s.capitalize() for s in module.split("_"))

        self.start_urls = [url]
        self.automatically_set_parameters()

        tvars = {
            "project_name": self.settings.get("BOT_NAME"),
            "ProjectName": string_camelcase(self.settings.get("BOT_NAME")),
            "module": module,
            "name": name,
            "url": url,
            "domain": extract_domain(url),
            "classname": f"{capitalized_module}Spider",
        }
        # Flatten the parameters and merge with the other variables
        return tvars | self.parameters

    # TODO: If https://github.com/scrapy/scrapy/pull/6470 is merged, much of this can be removed
    def _genspider(
        self,
        module: str,
        name: str,
        url: str,
        template_name: str,
        template_file: Union[str, os.PathLike],
    ) -> None:
        """Generate the spider module, based on the given template"""
        tvars = self._generate_template_variables(module, name, url, template_name)
        if self.settings.get("NEWSPIDER_MODULE"):
            spiders_module = import_module(self.settings["NEWSPIDER_MODULE"])
            assert spiders_module.__file__
            spiders_dir = Path(spiders_module.__file__).parent.resolve()
        else:
            spiders_module = None
            spiders_dir = Path(".")
        spider_file = f"{spiders_dir / module}.py"
        shutil.copyfile(template_file, spider_file)
        render_templatefile(spider_file, **tvars)
        print(
            f"Created spider {name!r} using template {template_name!r} ",
            end=("" if spiders_module else "\n"),
        )
        if spiders_module:
            print(f"in module:\n  {spiders_module.__name__}.{module}")
