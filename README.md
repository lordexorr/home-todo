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
Assistant theme, light or dark. After an update, a Home To-Do page that was already open asks to be reloaded.

## Lists

- **Mine** is each person's own list. Only they see it, administrators included, unless they put it on Home
  Assistant's calendar.
- **Family** is shared: everyone who uses Home To-Do sees it and can change it, unless an administrator makes it view
  only, or hides it, for some people under **Configure**. Home Assistant shows every calendar to everyone, so the
  Family calendar still shows Family's due dates to people it's hidden from.

Switch between them with the buttons beside the logo. Each list has its own tasks, log, scratchpad, task numbers and
categories, so categories made on Mine stay private.

## Requests

A Family task can be for someone: choose them with **For** beside the due date, in the task's details, or with
`>Name` in the command bar, such as `add >Col Pick up the dry cleaning ^fri`. The start of a name is enough, and anyone
with a Home Assistant login can be chosen. Everyone sees who each Family task is for.

The person it's for is told on their phone, and whoever asked is told when it's done. Each person chooses where their
notifications go under **Settings** on Home To-Do's page: a phone with Home Assistant's app, or Home Assistant's own
notifications. Tapping one on a phone opens Home To-Do. Tasks for you are marked, the **Family** button counts them,
and they're on your own calendar if you've turned it on.

## Links to areas and devices

A task can be linked to an area or a device in Home Assistant, such as "Replace the filter" and the furnace: choose it
under **Link** in the task's details, or type `link 12 furnace` in the command bar. The task shows what it's linked to,
which administrators can click to open in Home Assistant. `find` searches it, the log keeps it, and the task's calendar
event names it.

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

Log entries more than a year old move to an archive overnight, so the page stays quick as the log grows. **Show
older entries** at the end of the log brings them back to read, and **Export** includes them.

If two people change the same notes or scratchpad at the same moment, both people's lines are kept, and where both
changed the same line, both versions are.

While Home Assistant can't be reached, the page says so, and can't be edited until it's back.

## Removing Home To-Do

Removing Home To-Do, from **Settings → Devices & services** or from the Marketplace, keeps every list: they stay in
`.storage/home_todo`, and adding Home To-Do again brings them back. To delete the lists for good, delete that file
as well.
