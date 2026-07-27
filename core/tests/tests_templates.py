from pathlib import Path
from unittest import TestCase


class NoteListTemplateTests(TestCase):
    def test_empty_notes_row_accounts_for_optional_child_column(self):
        template = (
            Path(__file__).parents[1] / "templates" / "core" / "note_list.html"
        ).read_text()

        self.assertIn(
            '<th colspan="{% if not unique_child %} 6 {% else %} 5 {% endif %}">',
            template,
        )
