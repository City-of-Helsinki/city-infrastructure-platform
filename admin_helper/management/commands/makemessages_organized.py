from django.core.management.commands import makemessages


class Command(makemessages.Command):
    """Explicitly configure makemessages command to produce strings sorted by ID and eliminate fuzzy matches."""

    # xgettext --help for more information
    xgettext_options = makemessages.Command.xgettext_options + ["--sort-output"]
    # msgmerge --help for more information
    msgmerge_options = makemessages.Command.msgmerge_options + ["--no-fuzzy-matching"]
