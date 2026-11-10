# Changelog

## 0.6.0

- **New: Control who sees the Family list.** Under **Configure**, an administrator can make Family view only for some people, or hide it from them. People who can only view it can't be given requests. Home Assistant's calendar still shows Family's due dates to everyone.
- **New: Link a task to an area or device.** Choose it under **Link** in the task's details, or type `link 12 furnace`. Administrators can click the link to open that area or device. `find` searches links, and the log and calendar keep them.
- **Improved: Undo after removing a category** from the category picker.
- **Fix: A task ticked off on two devices at once** is now logged once, not twice.
- **Fix: Devices & services shows the name set under Configure**, not "Home To-Do".
- **Behind the scenes: Code tidy-up.** Nothing changes for you.

## 0.5.0

- **New: Requests.** A Family task can be for someone: choose them with **For** beside the due date, in the task's details, or with `>Name` in the command bar, such as `add >Col Pick up the dry cleaning ^fri`. They're notified, and you're notified when they've done it. Tasks for you are marked, and the **Family** button counts them.
- **New: Choose where you're notified.** Open the menu beside the clock, choose **Settings**, and pick your phone under **Notify me on**. Everyone picks their own. Tapping a notification opens Home To-Do.
- **New: Make an existing task a request.** Click a Family task and choose someone under **For** in its details, or **Anyone** to take it off them. `for 12 Colleen` and `for 12 none` do the same in the command bar.
- **Improved: Requests for you are on your own calendar**, if you've turned it on.

## 0.4.0

- **Improved: Stays quick as lists grow.** Each change sends open pages only what changed, not the whole list.
- **New: Older log entries are archived.** Entries more than a year old move to an archive overnight. **Show older entries** at the end of the log brings them back, and **Export** includes them.
- **Improved: Two people can edit the same notes at once.** Both people's lines are kept, and where both changed the same line, both versions are kept.
- **Fix: Someone else's change no longer moves your cursor** or drops you out of a side task you're typing in.

## 0.3.2

- **Changed: Each list has its own categories**, so categories made on Mine stay private. Existing categories went to the lists that use them, and unused ones to Family.
- **New: An open page asks you to reload after an update**, instead of carrying on with the old version.
- **Fix: Edits from a page opened before an update** no longer erase newer settings, such as a task's repeat.
- **Fix: A quick double tap on a repeating task** no longer completes it twice.
- **Fix: On a page left open overnight**, the log's date now moves on to the new day.
- **Fix: A shortcut typed without `https://`** now appears, with `https://` added. One that isn't a web address, such as `mailto:`, isn't kept.

## 0.3.1

- **New: An example shortcut.** The top bar starts with **Trash schedule**, to show what shortcuts are for. Change or remove it under **Settings**.
- **Improved: Clearer hints** in an empty shortcut row.

## 0.3.0

- **New: Repeating tasks.** A task can repeat every so many days, weeks, months or years: use the ↻ button beside the due date, the task's details, or `*1w` or `~3mo` in the command bar. **On a schedule** counts from the due date; **after it's done** counts from when you tick it off. Ticking one off logs it and brings it back with its next due date.
- **New: Family on Home Assistant's calendar.** Family's tasks with a due date appear as **Home To-Do Family**, including scheduled repeats. Automations can use it like any calendar.
- **New: Your own list on the calendar**, if you turn it on under **Settings**. It's off by default, since Home Assistant shows every calendar to everyone.

## 0.2.1

- **Changed: The page uses Home Assistant's colors**, from each person's theme. Dark is Home Assistant's black, and buttons and highlights are its blue. Custom themes carry over.

## 0.2.0

- **New: Its own name.** The page and sidebar say **Home To-Do**, and **Configure** can change it for everyone, such as "Lowry Home To-Do".
- **Changed: Light and dark follow Home Assistant**, for each person. The theme button is gone.
- **New: Sort by, then by.** Sort by due date, priority, category or age, then by a second of those. Each person's choice is saved.
- **New: Export log (.txt)** saves what got done, by day.
- **Changed: Made for the household.** Examples, hints, placeholders and the logo are about the house, and work-only features are gone.
- **Improved: Top-bar shortcuts** take any web address, set under **Settings**.

## 0.1.0

The first release: task lists for the house, on a page in Home Assistant's sidebar.

- **New: Mine and Family.** Everyone has their own private list and shares the Family list. Switch with the buttons beside the logo.
- **New: Kept in Home Assistant.** Every change is saved in `.storage/home_todo` and shows straight away on every device with the same list open. Home Assistant's backups include it.
- **New: Your display settings follow you** to every device, such as panel widths, sort order and which list was open.
- **New: Offline notice.** While Home Assistant can't be reached, the page says so and can't be edited until it's back.
- **New: Removing Home To-Do keeps the lists**, so adding it again brings them back.
- **New: On a phone, the menu button** at the top left opens Home Assistant's sidebar.
