"""Read-only finance-agent queries over one pinned, rule-interpreted snapshot."""
import json
from datetime import date
from collections import defaultdict
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import calculations as calc


class Scope(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, str_strip_whitespace=True)
    period: Literal['this_month', 'last_month', 'last_3', 'last_6', 'last_12', 'ytd', 'all'] | None = 'this_month'
    start: str | None = Field(default=None, pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    end: str | None = Field(default=None, pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    category: str | None = Field(default=None, min_length=1, max_length=120)
    merchant: str | None = Field(default=None, min_length=1, max_length=120)


class Breakdown(Scope):
    group_by: Literal['category', 'merchant'] = 'category'
    limit: int = Field(default=15, ge=1, le=20)
    offset: int = Field(default=0, ge=0, le=20000)


class Transactions(Scope):
    search: str | None = Field(default=None, min_length=1, max_length=120)
    type: Literal['Income', 'Expense', 'Refund', 'Transfer'] | None = None
    limit: int = Field(default=10, ge=1, le=15)
    offset: int = Field(default=0, ge=0, le=20000)


class Compare(Scope):
    compare_start: str = Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    compare_end: str = Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')


class Status(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    topic: Literal['net_worth', 'sinking_funds', 'verified_budget', 'rules']


TOOLS = {
    'get_financial_totals': (Scope, 'Calculate exact income, gross spending, refunds and net for a period, optionally filtered by category or merchant. Use this for groceries last month. Case-insensitive exact category/merchant matching. For explicit start/end months omit period or set it null.'),
    'get_spending_breakdown': (Breakdown, 'Rank spending by category or merchant for a period. Returns gross spending separately from refunds and income, with pagination. Discover category/merchant names here. Explicit start/end overrides the default period when period is omitted.'),
    'get_monthly_cashflow': (Breakdown, 'Get monthly income, spending, refunds and net for a period, with pagination. Set period last_12 for a year of trends.'),
    'find_transactions': (Transactions, 'Find a small page of matching transactions, newest first. Use only when individual examples or detail are needed; totals and counts must come from get_financial_totals, never from summing this sample. Search matches merchant, description or ID. Transfers may be requested explicitly.'),
    'compare_spending': (Compare, 'Compare exact totals in two month ranges with identical category/merchant filters. The first range uses period or start/end; the second uses compare_start/compare_end. Janus computes the changes.'),
    'get_financial_status': (Status, 'Read net worth, sinking fund status, verified-budget availability or active financial rules, only if relevant to the question. AI-generated Budget-tab plans are session-only and unavailable here.'),
}


def tool_definitions():
    return [{'name': name, 'description': description, 'parameters': model.model_json_schema()} for name, (model, description) in TOOLS.items()]


class FinanceQueries:
    def __init__(self, snapshot, rules, today=None):
        self.snapshot = snapshot
        self.rules = rules
        self.today = today or calc.today_dublin()
        # Interpret full history once: sinking-fund recognition can cross years.
        self.rows = calc.derive_rows(rules, snapshot['rows'])
        self.months = sorted({r['month'] for r in self.rows if r.get('month')})
        self.provisional = calc.sinking_ledger(self.rows)['provisional']

    def overview(self, stale=False):
        start, end = calc.resolve_period('this_month', today=self.today)
        return {'today': self.today.isoformat(), 'timezone': 'Europe/Dublin', 'currency': 'EUR',
                'coverage': {'first_month': self.months[0] if self.months else None, 'last_month': self.months[-1] if self.months else None},
                'snapshot_id': self.snapshot['snapshot_id'], 'rule_set_version': self.snapshot['rule_set_version'],
                'imported_at': self.snapshot['fetched_at'], 'stale': stale, 'provisional': self.provisional,
                'this_month': {'start': start, 'end': end, 'has_recorded_rows': start in self.months, **self.totals(self.select(start, end))},
                'warning_count': len(self.snapshot.get('warnings', []))}

    def select(self, start, end, category=None, merchant=None):
        return [r for r in self.rows if (start is None or start <= (r.get('month') or '') <= end)
                and not r['derived']['excluded']
                and (not category or str(r['derived'].get('category') or 'Uncategorised').casefold() == category.casefold())
                and (not merchant or str(r.get('merchant') or 'Unknown').casefold() == merchant.casefold())]

    @staticmethod
    def totals(rows):
        totals = calc._totals(rows)
        # Make sign conventions explicit instead of asking the LLM to infer them.
        spent = sum((-Decimal(r['derived']['effective_budget_amount_eur']) for r in rows
                     if r['derived']['type'] == 'Expense' and Decimal(r['derived']['effective_budget_amount_eur']) < 0), Decimal(0))
        return {'income_eur': totals['income'], 'gross_spending_eur': calc._money(spent),
                'spending_signed_eur': totals['spending'], 'refunds_eur': totals['refunds'],
                'transfers_signed_eur': totals['transfers'], 'investment_signed_eur': totals['investment'],
                'net_eur': totals['net'], 'transaction_count': totals['rows']}

    def execute(self, name, arguments):
        if name not in TOOLS:
            return {'error': 'unknown_tool', 'message': 'Choose a listed read-only finance tool.'}, None
        try:
            if isinstance(arguments, str):
                if len(arguments.encode('utf-8')) > 8000:
                    raise ValueError()
                arguments = json.loads(arguments)
            args = TOOLS[name][0].model_validate(arguments)
            if isinstance(args, Status):
                return self.status(args.topic), {'label': {'net_worth': 'Net worth', 'sinking_funds': 'Sinking funds', 'verified_budget': 'Verified budget data', 'rules': 'Financial rules'}[args.topic]}
            # Explicit dates are natural to supply without also passing period=null.
            preset = args.period if 'period' in args.model_fields_set or not (args.start or args.end) else None
            start, end = calc.resolve_period(preset, args.start, args.end, today=self.today)
            if start:
                date.fromisoformat(start + '-01')
                date.fromisoformat(end + '-01')
                if (int(end[:4]) - int(start[:4])) * 12 + int(end[5:]) - int(start[5:]) > 239:
                    raise ValueError('Choose at most 240 months')
            if isinstance(args, Compare):
                other_start, other_end = calc.resolve_period(None, args.compare_start, args.compare_end, today=self.today)
                date.fromisoformat(other_start + '-01')
                date.fromisoformat(other_end + '-01')
                if (int(other_end[:4]) - int(other_start[:4])) * 12 + int(other_end[5:]) - int(other_start[5:]) > 239:
                    raise ValueError('Choose at most 240 months')
            rows = self.select(start, end, args.category, args.merchant)
        except (ValidationError, ValueError, TypeError, RecursionError):
            return {'error': 'invalid_arguments', 'message': 'Use the tool schema. Supply either a period or valid ordered start/end months. No account identifiers or arbitrary fields are accepted.'}, None
        effective_start = start or (self.months[0] if self.months else None)
        effective_end = end or (self.months[-1] if self.months else None)
        gaps = [m for m in calc.month_list(effective_start, effective_end) or [] if m not in self.months]
        envelope = {'period': {'start': effective_start, 'end': effective_end},
                    'filters': {'category': args.category, 'merchant': args.merchant},
                    'known_filters': {'category': not args.category or any(str(r['derived'].get('category') or 'Uncategorised').casefold() == args.category.casefold() for r in self.rows),
                                      'merchant': not args.merchant or any(str(r.get('merchant') or 'Unknown').casefold() == args.merchant.casefold() for r in self.rows)},
                    'currency': 'EUR', 'provisional': self.provisional,
                    'missing_months': gaps[:12], 'missing_month_count': len(gaps),
                    'note': 'Gross spending is positive; spending_signed_eur is signed. Refunds are separate. Missing months are not zero activity.'}
        labels = {'get_financial_totals': 'Financial totals', 'get_spending_breakdown': 'Spending breakdown',
                  'get_monthly_cashflow': 'Monthly cash flow', 'find_transactions': 'Matching transactions', 'compare_spending': 'Spending comparison'}
        source = {'label': labels[name], 'period': envelope['period'], 'category': args.category, 'merchant': args.merchant}
        if name == 'get_financial_totals':
            return {**envelope, 'totals': self.totals(rows)}, source
        if name == 'compare_spending':
            other = self.totals(self.select(other_start, other_end, args.category, args.merchant))
            other_gaps = [m for m in calc.month_list(other_start, other_end) if m not in self.months]
            current = self.totals(rows)
            source['comparison_period'] = {'start': other_start, 'end': other_end}
            return {**envelope, 'totals': current, 'comparison': {'period': source['comparison_period'], 'totals': other,
                    'missing_months': other_gaps[:12], 'missing_month_count': len(other_gaps)},
                    'change_eur': {k: calc._money(Decimal(current[k]) - Decimal(other[k])) for k in current if k.endswith('_eur')}}, source
        if name == 'find_transactions':
            matches = [r for r in rows if (not args.type or r['derived']['type'] == args.type)
                       and (not args.search or args.search.casefold() in ' '.join(str(r.get(k) or '') for k in ('merchant', 'description', 'transaction_id')).casefold())]
            matches.sort(key=lambda r: (r.get('date') or '', r.get('row') or 0), reverse=True)
            page = [{'date': r.get('date'), 'transaction_id': str(r.get('transaction_id') or '')[:80],
                     'merchant': str(r.get('merchant') or '')[:120], 'description': str(r.get('description') or '')[:160],
                     'category': r['derived'].get('category'), 'type': r['derived']['type'],
                     'amount_eur': r['derived']['effective_budget_amount_eur']} for r in matches[args.offset:args.offset + args.limit]]
        else:
            groups = defaultdict(list)
            for row in rows:
                if row['derived']['type'] not in calc.BUDGET_TYPES:
                    continue
                key = row.get('month') if name == 'get_monthly_cashflow' else (row['derived'].get('category') or 'Uncategorised') if args.group_by == 'category' else (row.get('merchant') or 'Unknown')
                groups[key].append(row)
            matches = [{'name': key, **self.totals(value)} for key, value in groups.items()]
            matches.sort(key=(lambda r: r['name']) if name == 'get_monthly_cashflow' else (lambda r: (-Decimal(r['gross_spending_eur']), r['name'])))
            page = matches[args.offset:args.offset + args.limit]
        source['returned_rows'] = len(page)
        return {**envelope, 'rows': page, 'total_rows': len(matches), 'offset': args.offset,
                'next_offset': args.offset + len(page) if args.offset + len(page) < len(matches) else None,
                'truncated': args.offset > 0 or args.offset + len(page) < len(matches)}, source

    def status(self, topic):
        base = {'currency': 'EUR', 'provisional': self.provisional}
        if topic == 'verified_budget':
            return {**base, 'available': False, 'reason': 'No verified ledger budget is configured. Budget-tab AI plans remain in the browser session and are not available to Ask.'}
        if topic == 'rules':
            return {**base, 'rules': [{k: r.get(k) for k in ('rule_id', 'name', 'field', 'operator', 'value', 'action', 'priority')} for r in self.rules[:20]],
                    'total_rules': len(self.rules), 'truncated': len(self.rules) > 20}
        if topic == 'sinking_funds':
            return {**base, 'status': calc.sinking_ledger(self.rows)}
        worth = calc.parse_net_worth(self.snapshot.get('snapshot_grid'))
        return {**base, **({'available': True, 'latest': worth['latest'], 'history': worth['history'][-6:]} if worth.get('available') else worth)}
