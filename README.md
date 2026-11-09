# Home To-Do

Task lists for the house, on a page in Home Assistant's sidebar. Everyone has their own list, **Mine**, and shares
the **Family** list. Tasks have a priority, a due date, a category and side tasks. Finished ones move to a completed
log, grouped by day. Each task and log entry has its own notes, beside a scratchpad for each list.

## Install

Home To-Do needs Home Assistant 2026.11 or later, and is installed through its Marketplace.

1. In the **Marketplace**, choose **Add from a GitHub link** and enter `https://github.com/lordexorr/home-todo`, as an **Integration** if it asks.
2. Open **Home To-Do** in the Marketplace and download it.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and choose **Home To-Do**.

**Home To-Do** then appears in the sidebar for every user. **Configure** on its entry changes the name shown at the
top of the page and in the sidebar, such as "Lowry Home To-Do". Light and dark follow each person's Home Assistant
setting.

## Lists

- **Mine** is each person's own list. Only they see it, administrators included.
- **Family** is shared: everyone who uses Home To-Do sees it and can change it.

Switch between them with the buttons beside the logo. Each list has its own tasks, log and scratchpad, and its own
task numbers. Categories are shared by both.

## Where the lists are kept

Everything is kept in Home Assistant, in `.storage/home_todo` in its config folder, and Home Assistant's backups
include it. Changes are saved as they're made, and appear straight away on every other device showing the same
list. Each person's display settings, such as the theme and panel widths, are kept there too.

While Home Assistant can't be reached, the page says so, and can't be edited until it's back.

## Removing Home To-Do

Removing Home To-Do, from **Settings → Devices & services** or from the Marketplace, keeps every list: they stay in
`.storage/home_todo`, and adding Home To-Do again brings them back. To delete the lists for good, delete that file
as well.
