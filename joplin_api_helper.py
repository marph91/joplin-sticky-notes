from __future__ import annotations

import json

from joppy.api import Api
import requests


def request_api_token():

    # TODO: Make more robust.

    try:
        response = requests.post("http://localhost:41184/auth")
        if response.status_code == 200:
            auth_token = response.json()["auth_token"]
    except requests.exceptions.ConnectionError:
        pass

    for _ in range(30):
        response = requests.get(
            f"http://localhost:41184/auth/check?auth_token={auth_token}"
        )
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "accepted":
                return data["token"]
        time.sleep(1)
    return None


def setup_joplin():
    settings_file = Path().home() / ".joplin-sticky-notes/settings.json"
    if settings_file.exists():
        with open(settings_file) as infile:
            settings = json.load(infile)
        if (api_token := settings.get("api_token")) is None:
            api_token = request_api_token()
    else:
        settings_file.parent.mkdir(exist_ok=True)
        api_token = request_api_token()

    with open(settings_file, "w") as outfile:
        json.dump({"api_token": api_token}, outfile, indent=2)

    return Api(token=api_token)


import joppy.data_types as dt
import argparse
from collections import defaultdict
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import List


@dataclass
class TreeItem:
    """Represents a notebook and its children."""

    data: dt.NotebookData
    child_items: List[TreeItem]
    child_notes: List[dt.NoteData]
    # child_resources: List[dt.ResourceData]


def create_notebook_tree(flat_list):
    """
    Create a tree of IDs from a flat list.
    Based on https://stackoverflow.com/a/45461474/7410886.
    """
    graph = {item: set() for item in flat_list}
    roots = []
    for id_, item in flat_list.items():
        parent_id = item.parent_id
        if parent_id:
            graph[parent_id].add(id_)
        else:
            roots.append(id_)

    def traverse(graph, names):
        hierarchy = {}
        for name in names:
            hierarchy[name] = traverse(graph, graph[name])
        return hierarchy

    return traverse(graph, roots)


def create_hierarchy(api):
    """
    Create a notebook hierarchy (including notes and resources)
    from a flat notebook list.
    """
    # Don't use "as_tree=True", since it's undocumented and might be removed.
    notebooks_flat_api = api.get_all_notebooks(fields="id,title,parent_id")
    notebooks_flat_map = {notebook.id: notebook for notebook in notebooks_flat_api}
    notebook_tree_ids = create_notebook_tree(notebooks_flat_map)

    item_count = defaultdict(int)

    def replace_ids_by_items(id_tree):
        item_tree = []
        for key, value in id_tree.items():
            item_count["notebooks"] += 1
            child_notes = api.get_all_notes(notebook_id=key, fields="id,title")
            # child_resources = []
            # for note in child_notes:
            #    child_resources.extend(
            #        api.get_all_resources(note_id=note.id, fields="id,title")
            #    )

            item_count["notes"] += len(child_notes)
            # item_count["resources"] += len(child_resources)
            item_tree.append(
                TreeItem(
                    notebooks_flat_map[key],
                    replace_ids_by_items(value),
                    child_notes,
                    # child_resources,
                )
            )
        return item_tree

    notebook_tree_items = replace_ids_by_items(notebook_tree_ids)
    return notebook_tree_items
