#!/usr/bin/env python3
"""Hide/show folders in workspace
"""

import os
import sys
from pathlib import Path
from typing import Any

import anyconfig
import pyjson5
import vscode
from addict import Dict as AttrDict
from vscode.context import Context

ext = vscode.Extension(name="Hide Folder")


@ext.event
async def on_activate():
    """Run at extension activation."""
    vscode.log(f"The Extension '{ext.name}' has started.")


async def show_info(ctx: Context, msg: Any) -> None:
    """Show information message.

    Args:
        ctx (Context): Current context.
        msg (Any): Message to show. It will be converted to string.
    """
    await ctx.show(vscode.InfoMessage(f"{ext.name}: {str(msg)}"))


async def show_error(ctx: Context, msg: Any) -> None:
    """Show error message.

    Args:
        ctx (Context): Current context.
        msg (Any): Message to show. It will be converted to string.
    """
    await ctx.show(vscode.ErrorMessage(f"{ext.name}: {str(msg)}"))


async def get_workspace_json(ctx: Context) -> Path:
    """Get workspace setting JSON file path.

    Args:
        ctx (Context): Current context

    Returns:
        Path: The workspace JSON file path
    """
    try:
        json_path = Path(
            await ext.ws.run_code(
                "vscode.workspace.workspaceFile.path",
                thenable=False,
            ),
        )
        if not json_path.is_file():
            await show_error(ctx, f"{json_path} does not exist.")
            return Path()
    except Exception as exc:  # pylint: disable=broad-except
        await show_error(ctx, exc)
        return Path()

    return json_path


async def read_workspace_json(ctx: Context) -> AttrDict:
    """Read the workspace JSON file without comments.

    Args:
        ctx (Context): Current context

    Returns:
        AttrDict: The workspace JSON
    """
    json_path = await get_workspace_json(ctx)

    with open(json_path, "r", encoding="utf-8", errors="ignore") as fp:
        json_dict = AttrDict(pyjson5.load(fp))  # pylint: disable=no-member

    return json_dict


async def write_workspace_json(ctx: Context, json_dict: dict) -> None:
    """Read the workspace JSON file without comments.

    Args:
        ctx (Context): Current context
        json_dict (dict): The workspace JSON
    """
    json_path = await get_workspace_json(ctx)
    anyconfig.dump(json_dict, json_path, "json", indent=4)
    return json_dict


@ext.command()
async def hide_folder(ctx: Context):
    """Hide folder in workspace.

    Args:
        ctx (Context): Current context.
    """
    json_dict = await read_workspace_json(ctx)

    if len(json_dict.folders) < 2:
        return await show_error(ctx, "Cannot hide the last folder.")

    # find the folder to hide
    one_ws_folder = await ext.ws.run_code(
        """
        vscode.commands.executeCommand('copyFilePath')
        vscode.env.clipboard.readText()
        """,
        thenable=True,
    )

    # get workspace root path
    ws_root = await ext.ws.run_code(
        "vscode.workspace.rootPath",
        thenable=False,
    )

    # change to workspace root path for relative paths
    os.chdir(ws_root)

    # get absolute path of the folder to hide
    one_ws_folder = Path(one_ws_folder).resolve()

    if not one_ws_folder.is_dir():
        return

    # region: hide the folder by moving it to hidden_folders setting section
    abs_folders = []

    # hidden folders in workspace
    hidden_folders = json_dict.settings.get(f"{ext.name}.hidden_folders", [])

    for one_folder in json_dict.folders:
        new_folder_dict = AttrDict()

        # update path to absolute path
        new_folder_dict.path = str(Path(one_folder.path).resolve())

        # update name if exists
        if one_folder.name:
            new_folder_dict.name = one_folder.name

        # record the folder in hidden_folders setting section
        if new_folder_dict.path == str(one_ws_folder):
            hidden_folders.append(new_folder_dict)
            continue

        # dont touch other folders
        abs_folders.append(new_folder_dict)

    json_dict.settings[f"{ext.name}.hidden_folders"] = hidden_folders
    json_dict.folders = abs_folders
    # endregion: hide the folder by moving it to hidden_folders setting section

    await write_workspace_json(ctx, json_dict)

    return await show_info(ctx, f"{one_ws_folder} is hidden.")


@ext.command()
async def show_folder(ctx: Context):
    """Show folder in workspace.

    Args:
        ctx (Context): Current context.
    """
    json_dict = await read_workspace_json(ctx)

    # hidden folders in workspace
    hidden_folders = json_dict.settings.get(f"{ext.name}.hidden_folders", [])

    paths = [one_folder.path for one_folder in hidden_folders]

    if not paths:
        return await show_error(ctx, "No hidden folders to show.")

    path_to_show = await ext.ws.run_code(
        f"""
            vscode.window.showQuickPick(
                {paths},
                {{
                    placeHolder: 'Select a folder to show'
                }}
            )
        """,
        thenable=True,
    )

    # show folder
    for one_folder in hidden_folders:
        if one_folder.path != path_to_show:
            continue
        if one_folder not in json_dict.folders:
            json_dict.folders += [one_folder]
        break

    # remove folder from hidden_folders
    json_dict.settings[f"{ext.name}.hidden_folders"] = []

    for one_folder in hidden_folders:
        if one_folder.path == path_to_show:
            continue
        json_dict.settings[f"{ext.name}.hidden_folders"] += [one_folder]

    await write_workspace_json(ctx, json_dict)

    return await show_info(ctx, f"Showing {path_to_show}")


def update_package_json() -> None:
    """Update package.json."""

    repo_root = Path(__file__).resolve().parent
    package_json = AttrDict(anyconfig.load(repo_root / "package.json"))
    package_json.displayName = "Hide Folder"
    package_json.description = __doc__.strip()
    for cmd in package_json.contributes.commands:
        if cmd.command == f"{ext.name}.hideFolder":
            cmd.title = "Hide Folder in workspace"
        if cmd.command == f"{ext.name}.showFolder":
            cmd.title = "Show Folder in workspace"
    package_json.contributes.configuration = {
        "title": ext.name,
        "properties": {
            f"{ext.name}.hidden_folders": {
                "type": "array",
                "default": [],
                "description": "Hidden folder in workspace",
            }
        },
    }
    package_json.contributes.menus["explorer/context"] = [
        {
            "when": "workbenchState == workspace && explorerResourceIsRoot",
            "command": f"{ext.name}.hideFolder",
            "group": "2_workspace",
        },
        {
            "when": "workbenchState == workspace",
            "command": f"{ext.name}.showFolder",
            "group": "2_workspace",
        },
    ]
    package_json.repository = {
        "type": "git",
        "url": "https://github.com/zcold/hide-folder.git",
    }
    package_json.bugs = {
        "url": "https://github.com/zcold/hide-folder/issues",
    }
    package_json.publishers = ["semispot-ab"]
    package_json.homepage = "https://github.com/zcold/hide-folder/blob/main/README.md"
    package_json.license = "MIT"
    package_json.categories = ["Other"]
    package_json.keywords = ["vscode", "extension", "workspace", "folder", "hide"]
    package_json.extensionKind = ["workspace"]
    package_json.pricing = "free"

    anyconfig.dump(package_json, repo_root / "package.json", "json", indent=4)


if __name__ == "__main__":
    ext.run()

    # update package.json if not running as a vscode extension
    if "--run-webserver" not in sys.argv:
        update_package_json()
