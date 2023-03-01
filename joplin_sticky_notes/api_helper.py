from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import time
from typing import List

import joppy.data_types as dt
import requests


def request_api_token():

    # TODO: Make more robust.

    try:
        response = requests.post("http://localhost:41184/auth", timeout=5)
        if response.status_code == 200:
            auth_token = response.json()["auth_token"]
        else:
            return None
    except requests.exceptions.ConnectionError:
        return None

    for _ in range(60):
        response = requests.get(
            f"http://localhost:41184/auth/check?auth_token={auth_token}", timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "accepted":
                return data["token"]
        time.sleep(1)
    return None


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
    try:
        # Don't use "as_tree=True", since it's undocumented and might be removed.
        notebooks_flat_api = api.get_all_notebooks(fields="id,title,parent_id")
    except requests.exceptions.ConnectionError:
        return []
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
