import json
import unittest
from datetime import date
from types import SimpleNamespace as NS
from unittest.mock import patch

from core.finance.agent_queries import FinanceQueries, tool_definitions
from services import ai_service
from services.ai_tools import ToolCall, tool_result_messages
from test_finance_calc_api import row


class FinanceAgentQueryTests(unittest.TestCase):
    def setUp(self):
        rows = [row(month='2026-10', date='2026-10-06', category='Groceries', merchant='Market', amount_eur='-40.00'),
                row(month='2026-10', date='2026-10-07', category='Groceries', merchant='Market', type='Refund', amount_eur='5.00'),
                row(category='Groceries', merchant='Market', amount_eur='-90.00'),
                row(category='Salary', type='Income', amount_eur='1000.00'),
                row(category='Groceries', amount_eur='-999.00', include_provisional_totals='NO')]
        self.queries=FinanceQueries({'rows':rows,'snapshot_id':'test','rule_set_version':1,'fetched_at':'2026-11-25','warnings':[]},[],date(2026,11,25))

    def test_explicit_dates_refunds_and_unknown_filters(self):
        result,_=self.queries.execute('get_financial_totals',{'start':'2026-10','end':'2026-10','category':'groceries'})
        self.assertEqual(result['totals']['gross_spending_eur'],'40.00')
        self.assertEqual(result['totals']['refunds_eur'],'5.00')
        self.assertEqual(result['totals']['net_eur'],'-35.00')
        self.assertEqual(result['totals']['transaction_count'],2)
        unknown,_=self.queries.execute('get_financial_totals',{'category':'Unknown label'})
        self.assertFalse(unknown['known_filters']['category'])
        for bad in ({'start':'0000-01','end':'2026-01'}, {'start':'1900-01','end':'2026-11'}, {'period':'all','start':'2026-01','end':'2026-02'}):
            self.assertIn('error',self.queries.execute('get_financial_totals',bad)[0])

    def test_comparison_is_calculated_by_janus(self):
        result,_=self.queries.execute('compare_spending',{'category':'Groceries','period':'this_month','compare_start':'2026-10','compare_end':'2026-10'})
        self.assertEqual(result['change_eur']['gross_spending_eur'],'50.00')
        self.assertEqual(result['comparison']['period']['start'],'2026-10')

    def test_breakdown_and_transactions_are_explicitly_paginated(self):
        result,_=self.queries.execute('get_spending_breakdown',{'period':'all','limit':1})
        self.assertEqual(len(result['rows']),1)
        self.assertTrue(result['truncated'])
        self.assertEqual(result['next_offset'],1)
        result,_=self.queries.execute('find_transactions',{'period':'last_month','category':'Groceries','limit':1})
        self.assertEqual(result['total_rows'],2)
        self.assertEqual(result['rows'][0]['date'],'2026-10-07')
        self.assertTrue(result['truncated'])
        self.assertNotIn('account_id',json.dumps(result))

    def test_schema_has_no_write_tools_or_account_selector(self):
        definitions=tool_definitions()
        self.assertEqual(len(definitions),6)
        for tool in definitions:
            self.assertFalse(tool['parameters']['additionalProperties'])
            self.assertNotIn('account_id',tool['parameters']['properties'])


class FinanceAgentProviderTests(unittest.TestCase):
    def test_openai_native_tools_preserve_reasoning_and_disable_storage(self):
        reasoning=NS(type='reasoning')
        call=NS(type='function_call',call_id='call-one',name='get_financial_totals',arguments='{"period":"last_month"}')
        with patch('services.openai_service.OpenAI') as sdk:
            method=sdk.return_value.responses.create
            method.return_value=NS(output=[reasoning,call],output_text='',status='completed')
            result=ai_service.finance_agent_turn('system',[],tool_definitions(),'user@example.com','fake','openai','gpt-5.6-sol',tools_enabled=False)
            self.assertEqual(result.calls[0].id,'call-one')
            self.assertIs(result.continuation[0],reasoning)
            self.assertFalse(method.call_args.kwargs['store'])
            self.assertEqual(method.call_args.kwargs['tool_choice'],'none')
            self.assertIn('reasoning.encrypted_content',method.call_args.kwargs['include'])
            self.assertEqual(sdk.call_args.kwargs['max_retries'],0)

    def test_anthropic_native_tool_use_and_result_ids(self):
        block=NS(type='tool_use',id='call-one',name='get_financial_totals',input={'period':'last_month'})
        with patch('services.anthropic_service.Anthropic') as sdk:
            method=sdk.return_value.__enter__.return_value.messages.create
            method.return_value=NS(content=[block],stop_reason='tool_use')
            result=ai_service.finance_agent_turn('system',[],tool_definitions(),'user@example.com','fake','anthropic','claude-sonnet-5')
            self.assertEqual(result.calls[0].arguments,{'period':'last_month'})
            self.assertIn('input_schema',method.call_args.kwargs['tools'][0])
            continuation=tool_result_messages('anthropic',[(result.calls[0],'{}')])
            self.assertEqual(continuation[0]['content'][0]['tool_use_id'],'call-one')

    def test_mistral_native_calls_and_result_ids(self):
        call=NS(id='call-one',function=NS(name='get_financial_totals',arguments='{}'))
        message=NS(content='',tool_calls=[call],model_dump=lambda **kwargs: {'role':'assistant','content':'','tool_calls':[]})
        with patch('services.mistral_service.Mistral') as sdk:
            method=sdk.return_value.__enter__.return_value.chat.complete
            method.return_value=NS(choices=[NS(message=message,finish_reason='tool_calls')])
            result=ai_service.finance_agent_turn('system',[],tool_definitions(),'user@example.com','fake','mistral','mistral-small-2603')
            self.assertEqual(result.calls[0].name,'get_financial_totals')
            self.assertEqual(method.call_args.kwargs['timeout_ms'],20000)
            self.assertIsNone(method.call_args.kwargs['retries'])
            continuation=tool_result_messages('mistral',[(result.calls[0],'{}')])
            self.assertEqual(continuation[0]['tool_call_id'],'call-one')
            self.assertEqual(tool_result_messages('openai',[(result.calls[0],'{}')])[0]['call_id'],'call-one')
