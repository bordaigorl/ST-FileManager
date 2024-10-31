import os
import re

import sublime

TEMPLATE_FOLDER = None

# The UNESCAPED_DOLLAR regex matches a $ preceded by an even number of \
# (which would escape themselves and not the dollar)
# followed by a letter or underscore (without which the $ does not denote an expandable variable)
UNEXPANDED_VAR = re.compile(r'(?<!\\)(\\\\)*\$(\w|\d|_|\{)')


def md(*t, **kwargs):
    sublime.message_dialog(kwargs.get("sep", "\n").join([str(el) for el in t]))


def sm(*t, **kwargs):
    sublime.status_message(kwargs.get("sep", " ").join([str(el) for el in t]))


def em(*t, **kwargs):
    sublime.error_message(kwargs.get("sep", " ").join([str(el) for el in t]))


def isST3():
    return int(sublime.version()) > 3000


def get_settings():
    return sublime.load_settings("FileManager.sublime-settings")


def refresh_sidebar(settings=None, window=None):
    if window is None:
        window = sublime.active_window()
    if settings is None:
        settings = window.active_view().settings()
    if settings.get("explicitly_refresh_sidebar") is True:
        window.run_command("refresh_folder_list")


def get_template(created_file):
    """Return the right template for the create file"""
    global TEMPLATE_FOLDER

    if TEMPLATE_FOLDER is None:
        TEMPLATE_FOLDER = os.path.join(sublime.packages_path(), "User", ".FileManager")
        os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

    template_files = os.listdir(TEMPLATE_FOLDER)
    for item in template_files:
        if (
            os.path.splitext(item)[0] == "template"
            and os.path.splitext(item)[1] == os.path.splitext(created_file)[1]
        ):
            with open(os.path.join(TEMPLATE_FOLDER, item)) as fp:
                return fp.read()
    return ""


def yes_no_cancel_panel(
    message,
    yes,
    no,
    cancel,
    yes_text="Yes",
    no_text="No",
    cancel_text="Cancel",
    **kwargs
):
    loc = locals()
    if isinstance(message, list):
        message.append("Do not select this item")
    else:
        message = [message, "Do not select this item"]
    items = [message, yes_text, no_text, cancel_text]

    def get_max(item):
        return len(item)

    maxi = len(max(items, key=get_max))
    for i, item in enumerate(items):
        while len(items[i]) < maxi:
            items[i].append("")

    def on_done(index):
        if index in [-1, 3] and cancel:
            return cancel(*kwargs.get("args", []), **kwargs.get("kwargs", {}))
        elif index == 1 and yes:
            return yes(*kwargs.get("args", []), **kwargs.get("kwargs", {}))
        elif index == 2 and no:
            return no(*kwargs.get("args", []), **kwargs.get("kwargs", {}))
        elif index == 0:
            return yes_no_cancel_panel(**loc)

    window = sublime.active_window()
    window.show_quick_panel(items, on_done, 0, 1)


def transform_aliases(window, string):
    """Transform aliases using the settings and the default variables
    It's recursive, so you can use aliases *in* your aliases' values
    """

    vars = window.extract_variables()
    vars.update(get_settings().get("aliases"))

    string = string.replace("$$", "\\$")
    string = sublime.expand_variables(string, vars)
    expansion_count = 0
    while UNEXPANDED_VAR.search(string):
        expansion_count += 1
        if expansion_count > len(vars):
            return (False, string)
        string = sublime.expand_variables(string, vars)

    return (True, string)


def warn_invalid_aliases():
    sublime.error_message(
        "Invalid aliases: either your alias definitions are circular "
        "or your input was not escaping $ correctly (i.e. with $$)."
    )
    if get_settings().get("open_help_on_alias_infinite_loop", True) is True:
        sublime.run_command(
            "open_url",
            {
                "url": "https://github.com/math2001/ "
                "FileManager/wiki/Aliases "
                "#watch-out-for-infinite-loops"
            },
        )
