# Changelog

## 0.3.0

- **Repeating tasks:** a task can repeat every so many days, weeks, months or years, set with the new ↻ button beside the due date, in the task's details, or with `*1w` or `~3mo` in the command bar. **On a schedule** counts from the due date, so trash stays on Mondays even when it's done late; **after it's done** counts from the day it's ticked off, so the furnace filter is due three months after the last change. Ticking one off logs it and brings it straight back with its next due date and its side tasks unticked. `repeat # none` stops one repeating.
- **Home Assistant's calendar:** the Family list's tasks with a due date are on Home Assistant's calendar as **Home To-Do Family**, with scheduled repeats on each date they're coming up. Automations can use it like any calendar.
- **Your own list on the calendar:** each person can put their list there too, under **Settings**. It's off unless they turn it on, since Home Assistant shows every calendar to everyone who signs in.

## 0.2.1

- **Home Assistant's colors:** the page takes its colors from each person's Home Assistant theme. Dark is Home Assistant's black rather than a blue-grey, light is its light grey and white, and buttons and highlights are its blue. A custom theme carries over too. Priority, due dates and finished side tasks keep their own red, amber and green.

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
