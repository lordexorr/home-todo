# Home To-Do

Task lists for the house, on a page in Home Assistant's sidebar. Tasks have a priority, a due date, a category and
side tasks. Finished ones move to a completed log, grouped by day. Each task and log entry has its own notes, beside
a shared scratchpad.

## Install

Home To-Do needs Home Assistant 2026.11 or later, and is installed through its Marketplace.

1. In the **Marketplace**, choose **Add from a GitHub link** and enter `https://github.com/lordexorr/home-todo`, as an **Integration** if it asks.
2. Open **Home To-Do** in the Marketplace and download it.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and choose **Home To-Do**.

**Home To-Do** then appears in the sidebar for every user.

## Where the lists are kept

Each browser keeps its own lists, in its local storage. They aren't shared between browsers, devices or users, and
clearing the browser's data for Home Assistant deletes them.
