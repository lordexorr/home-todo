# Changelog

## 0.2.0

- **Its own name:** the page and the sidebar say **Home To-Do**. **Configure** on its entry changes the name for everyone, such as "Lowry Home To-Do", and says that removing Home To-Do keeps the lists.
- **Light and dark follow Home Assistant,** for each person, and change as soon as Home Assistant does. The theme button is gone.
- **Sort by, then by:** sort tasks by due date, priority, category or age, then by a second of those. Category sorts A–Z, with tasks that have no category last. Each person's choice is saved.
- **For the household:** ServiceNow tickets, with their links and setting, and the subnet calculator are gone. **Export log (.txt)** saves what got done, by day. Examples, hints and placeholders are about the house, the logo is a house with a check mark, and notes are in the regular font.
- **Top-bar shortcuts** take any web address, set under **Settings** in the menu beside the clock.

## 0.1.0

The first release: task lists for the house on a page in Home Assistant's sidebar, with everything kept in Home Assistant.

- **Mine and Family:** everyone has their own list, which only they see, administrators included, and shares the Family list, which everyone can change. Switch between them with the buttons beside the logo. Each list has its own tasks, log, scratchpad and task numbers; categories are shared by both.
- **Kept in Home Assistant:** every change is saved in `.storage/home_todo` as it's made, and shows straight away on every other device with the same list open. Home Assistant's backups include it.
- **Display settings,** such as the theme, panel widths, sort order and which list was open, are saved for each person, on every device.
- **Offline:** while Home Assistant can't be reached, the page says so and can't be edited until it's back.
- **Removing Home To-Do** keeps the lists, so adding it again brings them back. The README says how to delete them for good.
- **On a phone,** the menu button at the top left opens Home Assistant's sidebar.
