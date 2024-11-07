# Hide Folder

**This document is WIP.**

This VSCode extension show/hide folders in workspace. The motivation of this extension is that when we are working in a multi-root workspace with multiple roots, we may want to focus on a task that requires need few folders.

This extension is built using [vscode.py](https://pypi.org/project/vscode.py/).

## 1. Features

1. Show/Hide folders in workspace by updating the workspace file (`*.code-workspace`)
2. Trying to hide the last folder in workspace results an error message.
3. Trying to show folder while no hidden folders are in workspace does nothing.

## 2. Installation

### 2.1. Install from Github Repo

1. Prepare the extension folder

   ```bash
   git clone git@github.com:zcold/hide-folder.git
   cd hide-folder
   make_extension.sh
   ```

2. Launch VSCode and install the extension via command `Developer: Install Extension from Location...`

### 2.2. Install via VSCode Marketplace

**TBD**

## 3. Known issues

- Only supports installation in Linux via bash script
- Clipboard content is LOST when hiding folders due to limitation of VSCode API
  - https://github.com/microsoft/vscode/issues/3553
