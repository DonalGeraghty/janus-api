import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError
from services.ai_contract import HABIT_DRAFT_PROMPT, HabitDraftResponse
from services.ai_service import draft_habits
from services.ai_errors import AIBillingError
from services.openai_service import draft_habits as openai_draft
from services.mistral_service import draft_habits as mistral_draft
from services.anthropic_service import draft_habits as anthropic_draft

DRAFT = {'summary': 'A small evening routine.', 'habits': [{'name': 'Read', 'description': 'Read a little before bed.', 'icon': 'book', 'colour': '#d9c5a3', 'days': [0, 2, 4], 'category': 'Learning', 'group': 'Evening'}]}
CONTEXT = {'habits': [{'name': 'Walk'}], 'categories': ['Learning'], 'groups': ['Evening']}


class HabitProviderTests(unittest.TestCase):
    @patch('services.openai_service.OpenAI')
    def test_openai_sends_context_and_does_not_store_response(self, sdk):
        sdk.return_value.responses.parse.return_value.output_parsed = HabitDraftResponse.model_validate(DRAFT)
        self.assertEqual(openai_draft('Read more', CONTEXT, 'user@example.com', 'key', 'gpt-5.6-sol'), DRAFT)
        request = sdk.return_value.responses.parse.call_args.kwargs
        self.assertFalse(request['store'])
        self.assertEqual(request['input'][0]['content'], HABIT_DRAFT_PROMPT)
        self.assertEqual(json.loads(request['input'][1]['content'])['existing_habits'], CONTEXT['habits'])
        self.assertIs(request['text_format'], HabitDraftResponse)

    @patch('services.mistral_service.Mistral')
    def test_mistral_uses_same_validated_contract(self, sdk):
        client = sdk.return_value.__enter__.return_value
        client.chat.parse.return_value = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=DRAFT))])
        self.assertEqual(mistral_draft('Read more', CONTEXT, 'user@example.com', 'key', 'mistral-small-2603'), DRAFT)
        self.assertIs(client.chat.parse.call_args.kwargs['response_format'], HabitDraftResponse)

    @patch('services.anthropic_service.Anthropic')
    def test_anthropic_uses_same_validated_contract(self, sdk):
        client = sdk.return_value.__enter__.return_value
        client.messages.parse.return_value = SimpleNamespace(parsed_output=DRAFT, stop_reason='end_turn')
        self.assertEqual(anthropic_draft('Read more', CONTEXT, 'user@example.com', 'key', 'claude-sonnet-5'), DRAFT)
        self.assertIs(client.messages.parse.call_args.kwargs['output_format'], HabitDraftResponse)

    def test_dispatch_maps_provider_billing_failure(self):
        from services.openai_service import OpenAIBillingError
        with patch('services.openai_service.draft_habits', side_effect=OpenAIBillingError('credit')):
            with self.assertRaises(AIBillingError):
                draft_habits('Read', CONTEXT, 'user@example.com', 'key', 'openai', 'gpt-5.6-sol')

    def test_unusable_drafts_are_rejected(self):
        for change in [{'days': [7]}, {'days': [1, 1]}, {'colour': 'red'}, {'icon': 'invalid'}, {'name': ''}]:
            with self.assertRaises(ValidationError):
                HabitDraftResponse.model_validate({'summary': 'Draft', 'habits': [{**DRAFT['habits'][0], **change}]})
        self.assertEqual(HabitDraftResponse.model_validate({'summary': 'What routine do you want?', 'habits': []}).habits, [])
