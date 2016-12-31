from lib.common_libs.plugin import Plugin

class Help_Plugin(Plugin):
    """
    This plugin responsible for printing help to chat.
    """

    _info = {
        "name"          : "Help plugin",
        "shortname"     : "help_command_plugin",
        "description"   : "This plugin responsible for printing help to chat."
    }

    def __init__(self):
        Plugin.__init__(self)

        # Chat commands we will answer for.
        self.__chat_commands = {
            "help": {
                "keywords"      : ["help"],
                "description"   : "Show help message.",
                "method"        : self.show_help
            }
        }

    def get_commands(self):
        """
        Returns commands list we accept to caller.
        """
        return self.__chat_commands

    def initialize(self):
        """
        Help plugin initialization.
        """
        self.log(0, "Initializing plugin...")

    def show_help(self, message):
        """
        Returns help string.
        """
        help_string = ""
        cmds = self.loader.request_library("commands", "commands").get_commands()

        for cmd in cmds:
            # Format keywords in string.
            if len(cmds[cmd]["keywords"]) > 1:
                kwds = "`, `".join(cmds[cmd]["keywords"])
                help_string += kwds
            else:
                help_string += "`" + cmds[cmd]["keywords"][0] + "`"

            # Add description.
            help_string += " - " + cmds[cmd]["description"]

            # Add newline.
            help_string += "\n\n"

        return help_string
