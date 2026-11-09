"""Home To-Do's names."""
DOMAIN = "home_todo"
PANEL = "home-todo"  # the sidebar panel's address, /home-todo
STATIC_URL = "/home_todo_static"  # where the panel's files are served from

STORAGE_KEY = DOMAIN  # the lists are kept in .storage/home_todo
STORAGE_VERSION = 1
SAVE_DELAY = 1.0  # seconds after a change before it's written to disk

CONF_NAME = "name"  # shown at the top of the page and in the sidebar, set under Configure
DEFAULT_NAME = "Home To-Do"
NAME_MAX = 40
