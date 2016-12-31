from lib.common_libs.library import Library

class Commands(Library):

    _info = {
        "name"          : "Commands handling library",
        "shortname"     : "commands_library",
        "description"   : "Library responsible for handling commands."
    }

    def __init__(self):
        Library.__init__(self)
        self.__commands = {}

    def get_commands(self):
        """
        Returns self.__commands dict. Used by help plugin.
        """
        return self.__commands

    def init_library(self):
        """
        """
        self.log(0, "Initializing commands library...")

        # Get all plugins.
        plugins = self.loader.get_loaded_plugins()

        for plugin in plugins:
            cmds = plugins[plugin].get_commands()
            for cmd in cmds:
                if not cmd in self.__commands:
                    self.log(2, "Adding command {YELLOW}{cmd}{RESET}...", {"cmd": cmd})
                    self.__commands[cmd] = cmds[cmd]
                    self.__commands[cmd]["plugin_name"] = cmd
                else:
                    self.log(0, "{RED}ERROR:{RESET} command {YELLOW}{cmd}{RESET} already exists for plugin {BLUE}{plugin_name}{RESET}", {"cmd": cmd, "plugin_name": plugin})

        self.log(0, "We're accepting {CYAN}{commands_count}{RESET} commands", {"commands_count": len(self.__commands)})

    def process_command(self, command, message):
        """
        Processes command.
        """
        self.log(0, "Processing command {YELLOW}{command}{RESET} with data '{CYAN}{data}{RESET}'", {"command": command, "data": message})
        data = ""
        for cmd in self.__commands:
            if command in self.__commands[cmd]["keywords"]:
                data = self.__commands[cmd]["method"](message)
                return True, data

        return False, data
