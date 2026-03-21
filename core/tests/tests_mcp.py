# -*- coding: utf-8 -*-
import json

from django.test import TestCase, override_settings
from django.utils import timezone

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

User = get_user_model()
from core import models

MCP_ENDPOINT = "/api/mcp"


def _mcp_request(method, params=None, id=1):
    """Build a JSON-RPC 2.0 request body for MCP."""
    body = {
        "jsonrpc": "2.0",
        "method": method,
        "id": id,
    }
    if params is not None:
        body["params"] = params
    return body


class MCPEndpointTests(TestCase):
    """Tests for MCP endpoint accessibility and authentication."""

    fixtures = ["tests.json"]

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.first()
        self.token = Token.objects.create(user=self.user)

    def _post_mcp(self, data, **extra):
        return self.client.post(
            MCP_ENDPOINT,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            **extra,
        )

    def test_unauthenticated_request_rejected(self):
        """MCP endpoint requires authentication."""
        response = self._post_mcp(_mcp_request("initialize"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_request_accepted(self):
        """MCP endpoint accepts authenticated requests."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self._post_mcp(
            _mcp_request(
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_request(self):
        """MCP endpoint responds to authenticated GET."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(MCP_ENDPOINT, HTTP_ACCEPT="*/*")
        # GET may return 200 (SSE stream) or other valid status
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MCPToolListingTests(TestCase):
    """Tests for MCP tool discovery."""

    fixtures = ["tests.json"]

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.first()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        # Initialize the MCP session first
        self._post_mcp(
            _mcp_request(
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            )
        )

    def _post_mcp(self, data):
        return self.client.post(
            MCP_ENDPOINT,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )

    def test_list_tools(self):
        """Tools listing returns all registered tools."""
        response = self._post_mcp(_mcp_request("tools/list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("result", data)
        tools = data["result"]["tools"]
        tool_names = [t["name"] for t in tools]

        # Verify core tools exist
        expected_tools = [
            "list_children",
            "get_child",
            "create_child",
            "update_child",
            "delete_child",
            "list_feedings",
            "get_feeding",
            "log_feeding",
            "list_diaper_changes",
            "get_diaper_change",
            "log_diaper_change",
            "list_sleep",
            "get_sleep",
            "log_sleep",
            "list_temperatures",
            "log_temperature",
            "list_weights",
            "log_weight",
            "list_tummy_times",
            "log_tummy_time",
            "list_notes",
            "create_note",
            "list_timers",
            "start_timer",
            "stop_timer",
            "restart_timer",
            "get_daily_summary",
        ]
        for tool_name in expected_tools:
            self.assertIn(
                tool_name, tool_names, f"Tool '{tool_name}' not found in tool listing"
            )


class MCPToolCallTests(TestCase):
    """Tests for MCP tool invocations."""

    fixtures = ["tests.json"]

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.first()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        # Initialize session
        self._post_mcp(
            _mcp_request(
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            )
        )

    def _post_mcp(self, data):
        return self.client.post(
            MCP_ENDPOINT,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )

    def _call_tool(self, name, arguments=None):
        """Helper to call an MCP tool and return the response data."""
        params = {"name": name}
        if arguments:
            params["arguments"] = arguments
        response = self._post_mcp(_mcp_request("tools/call", params))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()

    def test_list_children(self):
        """list_children returns the test fixture child."""
        data = self._call_tool("list_children")
        self.assertIn("result", data)
        content = data["result"]["content"]
        self.assertTrue(len(content) > 0)

    def test_get_child(self):
        """get_child returns the correct child."""
        data = self._call_tool("get_child", {"slug": "fake-child"})
        self.assertIn("result", data)
        content = data["result"]["content"]
        self.assertTrue(len(content) > 0)

    def test_create_and_delete_child(self):
        """Create a child and then delete it."""
        data = self._call_tool(
            "create_child",
            {
                "first_name": "Test",
                "last_name": "Baby",
                "birth_date": "2024-01-01",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

        # Verify child exists
        child = models.Child.objects.get(slug="test-baby")
        self.assertEqual(child.first_name, "Test")

        # Delete
        data = self._call_tool("delete_child", {"slug": "test-baby"})
        self.assertIn("result", data)
        self.assertFalse(models.Child.objects.filter(slug="test-baby").exists())

    def test_log_diaper_change(self):
        """Log a diaper change via MCP."""
        now = timezone.now().isoformat()
        data = self._call_tool(
            "log_diaper_change",
            {
                "child_slug": "fake-child",
                "time": now,
                "wet": True,
                "solid": False,
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_get_daily_summary(self):
        """get_daily_summary returns a structured summary."""
        data = self._call_tool(
            "get_daily_summary",
            {
                "child_slug": "fake-child",
                "date": "2017-11-18",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_update_child(self):
        """Update a child's fields via MCP."""
        # Create a child to update so we don't affect other tests
        self._call_tool(
            "create_child",
            {"first_name": "Upd", "last_name": "Test", "birth_date": "2020-01-01"},
        )
        data = self._call_tool(
            "update_child",
            {
                "slug": "upd-test",
                "first_name": "Updated",
                "last_name": "Baby",
                "birth_date": "2020-06-15",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    # -- Feeding tools --

    def test_list_feedings(self):
        """list_feedings returns feedings."""
        data = self._call_tool("list_feedings")
        self.assertIn("result", data)
        content = data["result"]["content"]
        self.assertTrue(len(content) > 0)

    def test_list_feedings_filtered(self):
        """list_feedings with child_slug and date filters."""
        data = self._call_tool(
            "list_feedings",
            {"child_slug": "fake-child", "date": "2017-11-18"},
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_get_feeding(self):
        """get_feeding returns a specific feeding."""
        feeding = models.Feeding.objects.first()
        data = self._call_tool("get_feeding", {"id": feeding.id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_log_and_delete_feeding(self):
        """Log and delete a feeding via MCP."""
        data = self._call_tool(
            "log_feeding",
            {
                "child_slug": "fake-child",
                "start": "2024-01-01T10:00:00+00:00",
                "end": "2024-01-01T10:30:00+00:00",
                "type": "breast milk",
                "method": "left breast",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

        import json

        content = json.loads(data["result"]["content"][0]["text"])
        feeding_id = content["id"]

        # Delete
        data = self._call_tool("delete_feeding", {"id": feeding_id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))
        self.assertFalse(models.Feeding.objects.filter(id=feeding_id).exists())

    def test_update_feeding(self):
        """Update a feeding via MCP."""
        feeding = models.Feeding.objects.first()
        data = self._call_tool(
            "update_feeding",
            {
                "id": feeding.id,
                "child_slug": "fake-child",
                "start": "2017-11-18T14:00:00+00:00",
                "end": "2017-11-18T14:30:00+00:00",
                "type": "formula",
                "method": "bottle",
                "amount": 5.0,
                "notes": "updated via MCP",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_update_feeding_not_found(self):
        """Update nonexistent feeding returns error."""
        data = self._call_tool("update_feeding", {"id": 99999, "notes": "x"})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_delete_feeding_not_found(self):
        """Delete nonexistent feeding returns error."""
        data = self._call_tool("delete_feeding", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    # -- DiaperChange tools --

    def test_list_diaper_changes(self):
        """list_diaper_changes returns changes."""
        data = self._call_tool("list_diaper_changes")
        self.assertIn("result", data)
        content = data["result"]["content"]
        self.assertTrue(len(content) > 0)

    def test_list_diaper_changes_filtered(self):
        """list_diaper_changes with filters."""
        data = self._call_tool(
            "list_diaper_changes",
            {"child_slug": "fake-child", "wet": True, "solid": False},
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_get_diaper_change(self):
        """get_diaper_change returns a specific change."""
        dc = models.DiaperChange.objects.first()
        data = self._call_tool("get_diaper_change", {"id": dc.id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_update_diaper_change(self):
        """Update a diaper change via MCP."""
        dc = models.DiaperChange.objects.first()
        data = self._call_tool(
            "update_diaper_change",
            {
                "id": dc.id,
                "child_slug": "fake-child",
                "time": "2017-11-18T10:00:00+00:00",
                "wet": True,
                "solid": True,
                "color": "brown",
                "amount": 2.0,
                "notes": "updated via MCP",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_update_diaper_change_not_found(self):
        """Update nonexistent diaper change returns error."""
        data = self._call_tool("update_diaper_change", {"id": 99999, "notes": "x"})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_delete_diaper_change_not_found(self):
        """Delete nonexistent diaper change returns error."""
        data = self._call_tool("delete_diaper_change", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_delete_diaper_change(self):
        """Delete a diaper change via MCP."""
        now = timezone.now().isoformat()
        # Create one first
        data = self._call_tool(
            "log_diaper_change",
            {"child_slug": "fake-child", "time": now, "wet": True, "solid": False},
        )
        import json

        content = json.loads(data["result"]["content"][0]["text"])
        dc_id = content["id"]

        data = self._call_tool("delete_diaper_change", {"id": dc_id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))
        self.assertFalse(models.DiaperChange.objects.filter(id=dc_id).exists())

    # -- Sleep tools --

    def test_list_sleep(self):
        """list_sleep returns sleep records."""
        data = self._call_tool("list_sleep")
        self.assertIn("result", data)
        content = data["result"]["content"]
        self.assertTrue(len(content) > 0)

    def test_list_sleep_filtered(self):
        """list_sleep with child and date filters."""
        data = self._call_tool(
            "list_sleep",
            {"child_slug": "fake-child", "date": "2017-11-18"},
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_get_sleep(self):
        """get_sleep returns a specific sleep record."""
        sleep = models.Sleep.objects.first()
        data = self._call_tool("get_sleep", {"id": sleep.id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_log_and_delete_sleep(self):
        """Log and delete a sleep record via MCP."""
        data = self._call_tool(
            "log_sleep",
            {
                "child_slug": "fake-child",
                "start": "2024-01-01T20:00:00+00:00",
                "end": "2024-01-01T22:00:00+00:00",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

        import json

        content = json.loads(data["result"]["content"][0]["text"])
        sleep_id = content["id"]

        data = self._call_tool("delete_sleep", {"id": sleep_id})
        self.assertIn("result", data)
        self.assertFalse(models.Sleep.objects.filter(id=sleep_id).exists())

    def test_update_sleep(self):
        """Update a sleep record via MCP."""
        sleep = models.Sleep.objects.first()
        data = self._call_tool(
            "update_sleep",
            {
                "id": sleep.id,
                "child_slug": "fake-child",
                "start": sleep.start.isoformat(),
                "end": sleep.end.isoformat(),
                "notes": "updated via MCP",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_update_sleep_not_found(self):
        """Update nonexistent sleep returns error."""
        data = self._call_tool("update_sleep", {"id": 99999, "notes": "x"})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_delete_sleep_not_found(self):
        """Delete nonexistent sleep returns error."""
        data = self._call_tool("delete_sleep", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    # -- Temperature tools --

    def test_list_temperatures(self):
        """list_temperatures returns records."""
        data = self._call_tool("list_temperatures")
        self.assertIn("result", data)
        content = data["result"]["content"]
        self.assertTrue(len(content) > 0)

    def test_list_temperatures_filtered(self):
        """list_temperatures with filters."""
        data = self._call_tool(
            "list_temperatures",
            {"child_slug": "fake-child", "date": "2017-11-17"},
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_get_temperature(self):
        """get_temperature returns a specific record."""
        temp = models.Temperature.objects.first()
        data = self._call_tool("get_temperature", {"id": temp.id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_log_and_delete_temperature(self):
        """Log and delete a temperature via MCP."""
        data = self._call_tool(
            "log_temperature",
            {
                "child_slug": "fake-child",
                "temperature": 98.6,
                "time": "2024-01-01T10:00:00+00:00",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

        import json

        content = json.loads(data["result"]["content"][0]["text"])
        temp_id = content["id"]

        data = self._call_tool("delete_temperature", {"id": temp_id})
        self.assertIn("result", data)
        self.assertFalse(models.Temperature.objects.filter(id=temp_id).exists())

    def test_update_temperature(self):
        """Update a temperature via MCP."""
        temp = models.Temperature.objects.first()
        data = self._call_tool(
            "update_temperature",
            {
                "id": temp.id,
                "child_slug": "fake-child",
                "temperature": 99.1,
                "time": "2017-11-17T18:00:00+00:00",
                "notes": "updated",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_update_temperature_not_found(self):
        """Update nonexistent temperature returns error."""
        data = self._call_tool("update_temperature", {"id": 99999, "temperature": 99})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_delete_temperature_not_found(self):
        """Delete nonexistent temperature returns error."""
        data = self._call_tool("delete_temperature", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    # -- Weight tools --

    def test_list_weights(self):
        """list_weights returns records."""
        data = self._call_tool("list_weights")
        self.assertIn("result", data)
        content = data["result"]["content"]
        self.assertTrue(len(content) > 0)

    def test_list_weights_filtered(self):
        """list_weights with child filter."""
        data = self._call_tool("list_weights", {"child_slug": "fake-child"})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_get_weight(self):
        """get_weight returns a specific record."""
        weight = models.Weight.objects.first()
        data = self._call_tool("get_weight", {"id": weight.id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_log_and_delete_weight(self):
        """Log and delete a weight via MCP."""
        data = self._call_tool(
            "log_weight",
            {
                "child_slug": "fake-child",
                "weight": 10.5,
                "date": "2024-01-01",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

        import json

        content = json.loads(data["result"]["content"][0]["text"])
        weight_id = content["id"]

        data = self._call_tool("delete_weight", {"id": weight_id})
        self.assertIn("result", data)
        self.assertFalse(models.Weight.objects.filter(id=weight_id).exists())

    def test_update_weight(self):
        """Update a weight via MCP."""
        weight = models.Weight.objects.first()
        data = self._call_tool(
            "update_weight",
            {
                "id": weight.id,
                "child_slug": "fake-child",
                "weight": 11.0,
                "date": "2017-11-12",
                "notes": "updated",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_update_weight_not_found(self):
        """Update nonexistent weight returns error."""
        data = self._call_tool("update_weight", {"id": 99999, "weight": 10})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_delete_weight_not_found(self):
        """Delete nonexistent weight returns error."""
        data = self._call_tool("delete_weight", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    # -- TummyTime tools --

    def test_list_tummy_times(self):
        """list_tummy_times returns records."""
        data = self._call_tool("list_tummy_times")
        self.assertIn("result", data)
        content = data["result"]["content"]
        self.assertTrue(len(content) > 0)

    def test_list_tummy_times_filtered(self):
        """list_tummy_times with filters."""
        data = self._call_tool(
            "list_tummy_times",
            {"child_slug": "fake-child", "date": "2017-11-18"},
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_get_tummy_time(self):
        """get_tummy_time returns a specific record."""
        tt = models.TummyTime.objects.first()
        data = self._call_tool("get_tummy_time", {"id": tt.id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_log_and_delete_tummy_time(self):
        """Log and delete a tummy time via MCP."""
        data = self._call_tool(
            "log_tummy_time",
            {
                "child_slug": "fake-child",
                "start": "2024-01-01T10:00:00+00:00",
                "end": "2024-01-01T10:05:00+00:00",
                "milestone": "lifted head",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

        import json

        content = json.loads(data["result"]["content"][0]["text"])
        tt_id = content["id"]

        data = self._call_tool("delete_tummy_time", {"id": tt_id})
        self.assertIn("result", data)
        self.assertFalse(models.TummyTime.objects.filter(id=tt_id).exists())

    def test_update_tummy_time(self):
        """Update a tummy time via MCP."""
        tt = models.TummyTime.objects.first()
        data = self._call_tool(
            "update_tummy_time",
            {
                "id": tt.id,
                "child_slug": "fake-child",
                "start": tt.start.isoformat(),
                "end": tt.end.isoformat(),
                "milestone": "rolled over",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_update_tummy_time_not_found(self):
        """Update nonexistent tummy time returns error."""
        data = self._call_tool("update_tummy_time", {"id": 99999, "milestone": "x"})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_delete_tummy_time_not_found(self):
        """Delete nonexistent tummy time returns error."""
        data = self._call_tool("delete_tummy_time", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    # -- Note tools --

    def test_list_notes(self):
        """list_notes returns notes."""
        data = self._call_tool("list_notes")
        self.assertIn("result", data)
        content = data["result"]["content"]
        self.assertTrue(len(content) > 0)

    def test_list_notes_filtered(self):
        """list_notes with child filter."""
        data = self._call_tool("list_notes", {"child_slug": "fake-child"})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_get_note(self):
        """get_note returns a specific note."""
        note = models.Note.objects.first()
        data = self._call_tool("get_note", {"id": note.id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_create_update_delete_note(self):
        """Create, update, and delete a note via MCP."""
        data = self._call_tool(
            "create_note",
            {"child_slug": "fake-child", "note": "Test MCP note"},
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

        import json

        content = json.loads(data["result"]["content"][0]["text"])
        note_id = content["id"]

        # Update with all fields
        data = self._call_tool(
            "update_note",
            {"id": note_id, "child_slug": "fake-child", "note": "Updated MCP note"},
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

        # Delete
        data = self._call_tool("delete_note", {"id": note_id})
        self.assertIn("result", data)
        self.assertFalse(models.Note.objects.filter(id=note_id).exists())

    def test_update_note_not_found(self):
        """Update nonexistent note returns error."""
        data = self._call_tool("update_note", {"id": 99999, "note": "x"})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_delete_note_not_found(self):
        """Delete nonexistent note returns error."""
        data = self._call_tool("delete_note", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    # -- Timer tools --

    def test_list_timers(self):
        """list_timers returns timers."""
        data = self._call_tool("list_timers")
        self.assertIn("result", data)
        content = data["result"]["content"]
        self.assertTrue(len(content) > 0)

    def test_list_timers_filtered(self):
        """list_timers with active and child filters."""
        data = self._call_tool(
            "list_timers",
            {"active": True, "child_slug": "fake-child"},
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_get_timer(self):
        """get_timer returns a specific timer."""
        timer = models.Timer.objects.first()
        data = self._call_tool("get_timer", {"id": timer.id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

    def test_start_and_stop_timer(self):
        """Start and stop a timer via MCP."""
        data = self._call_tool(
            "start_timer",
            {
                "name": "Test Timer",
                "child_slug": "fake-child",
            },
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))

        # Find the created timer
        timer = models.Timer.objects.filter(name="Test Timer").first()
        self.assertIsNotNone(timer)
        self.assertTrue(timer.active)

        # Stop it (stopping deletes the timer)
        data = self._call_tool("stop_timer", {"id": timer.id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))
        self.assertFalse(models.Timer.objects.filter(id=timer.id).exists())

    def test_restart_timer(self):
        """Restart a timer via MCP."""
        timer = models.Timer.objects.first()
        original_start = timer.start
        data = self._call_tool("restart_timer", {"id": timer.id})
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))
        timer.refresh_from_db()
        self.assertNotEqual(timer.start, original_start)

    def test_delete_timer(self):
        """Delete a timer via MCP."""
        # Create a timer first
        data = self._call_tool(
            "start_timer",
            {"name": "To Delete"},
        )
        import json

        content = json.loads(data["result"]["content"][0]["text"])
        timer_id = content["id"]

        data = self._call_tool("delete_timer", {"id": timer_id})
        self.assertIn("result", data)
        self.assertFalse(models.Timer.objects.filter(id=timer_id).exists())

    # -- Error handling --

    def test_get_child_not_found(self):
        """get_child with invalid slug returns error."""
        data = self._call_tool("get_child", {"slug": "nonexistent"})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_get_feeding_not_found(self):
        """get_feeding with invalid id returns error."""
        data = self._call_tool("get_feeding", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_get_diaper_change_not_found(self):
        """get_diaper_change with invalid id returns error."""
        data = self._call_tool("get_diaper_change", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_get_sleep_not_found(self):
        """get_sleep with invalid id returns error."""
        data = self._call_tool("get_sleep", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_get_temperature_not_found(self):
        """get_temperature with invalid id returns error."""
        data = self._call_tool("get_temperature", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_get_weight_not_found(self):
        """get_weight with invalid id returns error."""
        data = self._call_tool("get_weight", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_get_tummy_time_not_found(self):
        """get_tummy_time with invalid id returns error."""
        data = self._call_tool("get_tummy_time", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_get_note_not_found(self):
        """get_note with invalid id returns error."""
        data = self._call_tool("get_note", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_get_timer_not_found(self):
        """get_timer with invalid id returns error."""
        data = self._call_tool("get_timer", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_stop_nonexistent_timer(self):
        """Stopping a nonexistent timer returns error."""
        data = self._call_tool("stop_timer", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_restart_timer_not_found(self):
        """Restart nonexistent timer returns error."""
        data = self._call_tool("restart_timer", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_delete_timer_not_found(self):
        """Delete nonexistent timer returns error."""
        data = self._call_tool("delete_timer", {"id": 99999})
        self.assertIn("result", data)
        self.assertTrue(data["result"].get("isError", False))

    def test_list_diaper_changes_date_filter(self):
        """list_diaper_changes with date filter."""
        data = self._call_tool(
            "list_diaper_changes",
            {"date": "2017-11-18"},
        )
        self.assertIn("result", data)
        self.assertFalse(data["result"].get("isError", False))


class MCPSerializerFieldTests(TestCase):
    """Tests that MCP tools return the expected DRF serializer fields."""

    fixtures = ["tests.json"]

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.first()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self._post_mcp(
            _mcp_request(
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            )
        )

    def _post_mcp(self, data):
        return self.client.post(
            MCP_ENDPOINT,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )

    def _call_tool(self, name, arguments=None):
        params = {"name": name}
        if arguments:
            params["arguments"] = arguments
        response = self._post_mcp(_mcp_request("tools/call", params))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()

    def _get_tool_result(self, name, arguments=None):
        """Call a tool and return the parsed JSON content."""
        data = self._call_tool(name, arguments)
        self.assertFalse(data["result"].get("isError", False))
        return json.loads(data["result"]["content"][0]["text"])

    def _get_tool_result_list(self, name, arguments=None):
        """Call a list tool and return a list by collecting all content blocks.

        The MCP SDK creates one content block per list item when a tool returns
        a list, so this helper assembles them back into a Python list.
        """
        data = self._call_tool(name, arguments)
        self.assertFalse(data["result"].get("isError", False))
        return [json.loads(block["text"]) for block in data["result"]["content"]]

    def test_child_fields(self):
        """get_child returns DRF ChildSerializer fields."""
        result = self._get_tool_result("get_child", {"slug": "fake-child"})
        expected = {
            "id",
            "first_name",
            "last_name",
            "birth_date",
            "birth_time",
            "slug",
            "picture",
        }
        self.assertEqual(set(result.keys()), expected)

    def test_feeding_fields(self):
        """get_feeding returns DRF FeedingSerializer fields."""
        feeding = models.Feeding.objects.first()
        result = self._get_tool_result("get_feeding", {"id": feeding.id})
        expected = {
            "id",
            "child",
            "start",
            "end",
            "duration",
            "type",
            "method",
            "amount",
            "notes",
            "tags",
        }
        self.assertEqual(set(result.keys()), expected)

    def test_diaper_change_fields(self):
        """get_diaper_change returns DRF DiaperChangeSerializer fields."""
        dc = models.DiaperChange.objects.first()
        result = self._get_tool_result("get_diaper_change", {"id": dc.id})
        expected = {
            "id",
            "child",
            "time",
            "wet",
            "solid",
            "color",
            "amount",
            "notes",
            "tags",
        }
        self.assertEqual(set(result.keys()), expected)

    def test_sleep_fields(self):
        """get_sleep returns DRF SleepSerializer fields."""
        sleep = models.Sleep.objects.first()
        result = self._get_tool_result("get_sleep", {"id": sleep.id})
        expected = {
            "id",
            "child",
            "start",
            "end",
            "duration",
            "nap",
            "notes",
            "tags",
        }
        self.assertEqual(set(result.keys()), expected)

    def test_temperature_fields(self):
        """get_temperature returns DRF TemperatureSerializer fields."""
        temp = models.Temperature.objects.first()
        result = self._get_tool_result("get_temperature", {"id": temp.id})
        expected = {"id", "child", "temperature", "time", "notes", "tags"}
        self.assertEqual(set(result.keys()), expected)

    def test_weight_fields(self):
        """get_weight returns DRF WeightSerializer fields."""
        weight = models.Weight.objects.first()
        result = self._get_tool_result("get_weight", {"id": weight.id})
        expected = {"id", "child", "weight", "date", "notes", "tags"}
        self.assertEqual(set(result.keys()), expected)

    def test_tummy_time_fields(self):
        """get_tummy_time returns DRF TummyTimeSerializer fields."""
        tt = models.TummyTime.objects.first()
        result = self._get_tool_result("get_tummy_time", {"id": tt.id})
        expected = {
            "id",
            "child",
            "start",
            "end",
            "duration",
            "milestone",
            "tags",
        }
        self.assertEqual(set(result.keys()), expected)

    def test_note_fields(self):
        """get_note returns DRF NoteSerializer fields."""
        note = models.Note.objects.first()
        result = self._get_tool_result("get_note", {"id": note.id})
        expected = {"id", "child", "note", "image", "time", "tags"}
        self.assertEqual(set(result.keys()), expected)

    def test_timer_fields(self):
        """get_timer returns DRF TimerSerializer fields."""
        timer = models.Timer.objects.first()
        result = self._get_tool_result("get_timer", {"id": timer.id})
        expected = {"id", "child", "name", "start", "duration", "user"}
        self.assertEqual(set(result.keys()), expected)

    def test_daily_summary_uses_serializer_fields(self):
        """get_daily_summary nested objects use DRF serializer fields."""
        result = self._get_tool_result(
            "get_daily_summary",
            {"child_slug": "fake-child", "date": "2017-11-18"},
        )
        # Child nested object should have DRF ChildSerializer fields
        child_keys = set(result["child"].keys())
        self.assertIn("birth_time", child_keys)
        self.assertIn("picture", child_keys)

        # Feeding last entry should have DRF FeedingSerializer fields
        if result["feeding"]["last"]:
            self.assertIn("tags", result["feeding"]["last"])
            self.assertIn("duration", result["feeding"]["last"])

        # Diaper change last entry
        if result["diaper_changes"]["last"]:
            self.assertIn("tags", result["diaper_changes"]["last"])

        # Sleep last entry
        if result["sleep"]["last"]:
            self.assertIn("tags", result["sleep"]["last"])
            self.assertIn("nap", result["sleep"]["last"])

    def test_list_children_fields(self):
        """list_children returns list with DRF serializer fields."""
        result = self._get_tool_result_list("list_children")
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        expected = {
            "id",
            "first_name",
            "last_name",
            "birth_date",
            "birth_time",
            "slug",
            "picture",
        }
        self.assertEqual(set(result[0].keys()), expected)

    def test_list_feedings_fields(self):
        """list_feedings returns list with DRF serializer fields."""
        result = self._get_tool_result_list("list_feedings")
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        expected = {
            "id",
            "child",
            "start",
            "end",
            "duration",
            "type",
            "method",
            "amount",
            "notes",
            "tags",
        }
        self.assertEqual(set(result[0].keys()), expected)
