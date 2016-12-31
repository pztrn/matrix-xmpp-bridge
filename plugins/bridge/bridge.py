from lib.common_libs.plugin import Plugin

HELP_MESSAGE = """**Creating a bridge**
To properly configure bridge you should issue command with following syntax:

```
bridge [matrix_room_id] [xmpp_user@domain] [xmpp_user_password] [muc@address.tld]
```

Where:

* `matrix_room_id` is room ID in Matrix. Check it out by pressing cogwheel near room's topic.
* `xmpp_user@domain` is XMPP JID which bot will use.
* `xmpp_user_password` is a password for XMPP JID.
* `muc@address.tld` is MUC address we will bridge.

Sit back. wait for couple of minutes and room will be bridged :)

**Listing all bridges you created**

Issue `bridge list` to get list of bridges you've created.
"""

class Bridge_Plugin(Plugin):
    """
    This plugin responsible for configuring of bridges.
    """

    _info = {
        "name"          : "Bridge plugin",
        "shortname"     : "help_command_plugin",
        "description"   : "This plugin responsible for configuring of bridges."
    }

    def __init__(self):
        Plugin.__init__(self)

        # Chat commands we will answer for.
        self.__chat_commands = {
            "bridge": {
                "keywords"      : ["bridge"],
                "description"   : "Manage bridges. Type 'bridge list' to get list of bridges configured by you.",
                "method"        : self.process
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

    def process(self, message):
        """
        Processes message.
        """
        if len(message) == 0:
            return self.show_help()
        else:
            return "Bridge configuration received message: " + message

    def show_help(self):
        """
        Returns help string.
        """
        return HELP_MESSAGE
