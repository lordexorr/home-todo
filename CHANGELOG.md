# Changelog

## 0.1.0

The first release: task lists for the house on a page in Home Assistant's sidebar, with everything kept in Home Assistant.

- **Mine and Family:** everyone has their own list, which only they see, administrators included, and shares the Family list, which everyone can change. Switch between them with the buttons beside the logo. Each list has its own tasks, log, scratchpad and task numbers; categories are shared by both.
- **Kept in Home Assistant:** every change is saved in `.storage/home_todo` as it's made, and shows straight away on every other device with the same list open. Home Assistant's backups include it.
- **Display settings,** such as the theme, panel widths, sort order and which list was open, are saved for each person, on every device.
- **Offline:** while Home Assistant can't be reached, the page says so and can't be edited until it's back.
- **Removing Home To-Do** keeps the lists, so adding it again brings them back. The README says how to delete them for good.
- **On a phone,** the menu button at the top left opens Home Assistant's sidebar.
