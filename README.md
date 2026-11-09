# Home To-Do

Task lists for the house, on a page in Home Assistant's sidebar. Everyone has their own list, **Mine**, and shares
the **Family** list. Tasks have a priority, a due date, a category and side tasks, and can repeat. Finished ones move
to a completed log, grouped by day. Each task and log entry has its own notes, beside a scratchpad for each list.
Tasks with a due date are on Home Assistant's calendar.

## Install

Home To-Do needs Home Assistant 2026.11 or later, and is installed through its Marketplace.

1. In the **Marketplace**, choose **Add from a GitHub link** and enter `https://github.com/lordexorr/home-todo`, as an **Integration** if it asks.
2. Open **Home To-Do** in the Marketplace and download it.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and choose **Home To-Do**.

**Home To-Do** then appears in the sidebar for every user. **Configure** on its entry changes the name shown at the
top of the page and in the sidebar, such as "Lowry Home To-Do". The page takes its colors from each person's Home
Assistant theme, light or dark.

## Lists

- **Mine** is each person's own list. Only they see it, administrators included, unless they put it on Home
  Assistant's calendar.
- **Family** is shared: everyone who uses Home To-Do sees it and can change it.

Switch between them with the buttons beside the logo. Each list has its own tasks, log and scratchpad, and its own
task numbers. Categories are shared by both.

## Repeating tasks

A task can repeat every so many days, weeks, months or years, set with the ↻ button beside its due date, in its
details, or in the command bar. Each repeating task counts its next due date one of two ways:

- **On a schedule** (`*` in the command bar) counts from the due date. `add Take out trash ^mon *1w` stays on Mondays
  even when it's done late, and one that's overdue moves to its next date that's still ahead.
- **After it's done** (`~`) counts from the day it's ticked off. `add Change furnace filter ~3mo` is due three months
  after the last change.

Ticking one off puts it in the completed log and brings it straight back with its next due date, its side tasks
unticked. A monthly one due on the 31st is due on the last day of shorter months.

## Home Assistant's calendar

The Family list's tasks with a due date are on Home Assistant's calendar, as **Home To-Do Family**, beside any other
calendars there. Each is an all-day event, and a task that repeats on a schedule shows on each date it's coming up.
Automations can use it like any calendar, such as for a morning reminder of what's due.

Each person can put their own list there too, under **Settings** in the menu beside the clock on Home To-Do's page.
It's off unless they turn it on: Home Assistant shows every calendar to everyone who signs in, so a personal list on
it is no longer private.

## Where the lists are kept

Everything is kept in Home Assistant, in `.storage/home_todo` in its config folder, and Home Assistant's backups
include it. Changes are saved as they're made, and appear straight away on every other device showing the same
list. Each person's display settings, such as panel widths and sort order, are kept there too.

While Home Assistant can't be reached, the page says so, and can't be edited until it's back.

## Removing Home To-Do

Removing Home To-Do, from **Settings → Devices & services** or from the Marketplace, keeps every list: they stay in
`.storage/home_todo`, and adding Home To-Do again brings them back. To delete the lists for good, delete that file
as well.
