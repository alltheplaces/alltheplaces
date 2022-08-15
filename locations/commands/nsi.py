from scrapy.commands import ScrapyCommand
from scrapy.exceptions import UsageError
from locations.name_suggestion_index import NSI


class NameSuggestionIndexCommand(ScrapyCommand):
    """
    Command to query the name suggestion index (NSI) by wikidata code or fuzzy name.
    Not only helps to see if NSI knows about a new brand that we may be writing a
    spider for but will also generate spider compatible code fragments. These can
    be pasted into the spider increasing keyboard life and reducing typo snafus.
    """

    requires_project = True
    default_settings = {"LOG_ENABLED": False}
    nsi = NSI()

    def syntax(self):
        return "[options] <name | code>"

    def short_desc(self):
        return "Lookup wikidata code or (fuzzy match) brand name in the name suggestion index"

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_argument(
            "--name",
            dest="lookup_name",
            action="store_true",
            help="Query NSI for matching brand name",
        )
        parser.add_argument(
            "--code",
            dest="lookup_code",
            action="store_true",
            help="Query NSI for wikidata code",
        )

    def run(self, args, opts):
        if not len(args) == 1:
            raise UsageError("please supply one and only one argument")
        if opts.lookup_name:
            self.lookup_name(args)
        if opts.lookup_code:
            self.lookup_code(args)

    def lookup_name(self, args):
        for k, v in self.nsi.lookup_label(args[0]):
            NameSuggestionIndexCommand.show(k, v)

    def lookup_code(self, args):
        if v := self.nsi.lookup_wikidata_code(args[0]):
            NameSuggestionIndexCommand.show(args[0], v)

    @staticmethod
    def show(code, data):
        print('"{0}", "{1}"'.format(data["label"], code))
        print("       -> https://www.wikidata.org/wiki/{}".format(code))
        print("       -> https://www.wikidata.org/wiki/Special:EntityData/{}.json".format(code))
        if s := data.get("description"):
            print("       -> {}".format(s))
        if s := data.get("identities"):
            print("       -> {}".format(s.get("website", "N/A")))
        print(
            '       -> item_attributes = {{"brand": "{0}", "brand_wikidata": "{1}"}}'.format(
                data["label"], code
            )
        )
