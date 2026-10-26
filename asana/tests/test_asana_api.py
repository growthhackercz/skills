#!/usr/bin/env python3
"""Provider-free behavior tests for the managed Asana helper."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "asana_api.py"
SPEC = importlib.util.spec_from_file_location("managed_asana_api", SCRIPT)
assert SPEC and SPEC.loader
ASANA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ASANA)


class AsanaReadFieldTests(unittest.TestCase):
    def invoke(self, *args: str) -> dict:
        calls: list[dict] = []

        def request(method, path, token, params=None, body=None):
            calls.append({
                "method": method,
                "path": path,
                "token": token,
                "params": params,
                "body": body,
            })
            return {"data": []}

        with (
            patch.object(ASANA, "credential", return_value="fixture-token"),
            patch.object(ASANA, "request_json", side_effect=request),
            patch.object(ASANA, "print_json", return_value=0),
            patch.object(sys, "argv", [str(SCRIPT), *args]),
        ):
            self.assertEqual(ASANA.main(), 0)
        self.assertEqual(len(calls), 1)
        return calls[0]

    def assert_task_fields(self, call: dict, *, detail: bool = False) -> None:
        fields = set(call["params"]["opt_fields"].split(","))
        expected = {
            "gid",
            "name",
            "notes",
            "resource_type",
            "completed",
            "assignee.name",
            "due_on",
            "permalink_url",
            "projects.name",
            "workspace.name",
            "memberships.section.name",
            "tags.name",
            "modified_at",
        }
        if detail:
            expected.add("created_at")
        self.assertEqual(fields, expected)

    def test_every_task_collection_includes_routing_fields(self) -> None:
        calls = [
            self.invoke("tasks-in-project", "--project", "project-1"),
            self.invoke("tasks-assigned", "--workspace", "workspace-1"),
            self.invoke("search-tasks", "--workspace", "workspace-1", "--text", "article"),
        ]
        for call in calls:
            with self.subTest(path=call["path"]):
                self.assertEqual(call["method"], "GET")
                self.assertEqual(call["params"]["limit"], 100)
                self.assert_task_fields(call)

    def test_task_detail_includes_routing_and_created_fields(self) -> None:
        call = self.invoke("task", "task-1")
        self.assertEqual(call["path"], "/tasks/task-1")
        self.assert_task_fields(call, detail=True)

    def test_project_collection_keeps_its_previous_fields(self) -> None:
        call = self.invoke("projects", "--workspace", "workspace-1")
        self.assertEqual(call["path"], "/projects")
        self.assertEqual(call["params"]["opt_fields"], ASANA.PROJECT_LIST_FIELDS)
        self.assertNotIn("notes", call["params"]["opt_fields"].split(","))
        self.assertNotIn("memberships.section.name", call["params"]["opt_fields"].split(","))
        self.assertNotIn("tags.name", call["params"]["opt_fields"].split(","))


if __name__ == "__main__":
    unittest.main()
