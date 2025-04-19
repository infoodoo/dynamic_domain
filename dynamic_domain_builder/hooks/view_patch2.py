from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from lxml import etree
from odoo.exceptions import ValidationError
from collections import defaultdict
from odoo.fields import Date, Datetime


class Base(models.AbstractModel):
    _inherit = 'base'


    @api.model
    def web_search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, count_limit=None):
        domain = domain or []
        is_from_search_more = self.env.context.get("is_from_search_more")

        if is_from_search_more:
            rules = self.env['field.domain.rule.line'].search([
                ('field_name.relation', '=', self._name),
                ('rule_id.active', '=', True),
                ('rule_id.user_id', '=', self.env.uid),
            ]) or self.env['field.domain.rule.line'].search([
                ('field_name.relation', '=', self._name),
                ('rule_id.active', '=', True),
                ('rule_id.user_id', '=', False),
            ])

            print(rules)

            for line in rules:
                try:
                    field = line.field_name
                    related_field = line.related_field_id
                    val = line.value
                    domain_key = related_field.name if related_field else 'id'

                    field_type = related_field.ttype if related_field else field.ttype

                    if line.operator in ['in', 'not in']:
                        try:
                            val = safe_eval(val)
                            if not isinstance(val, (list, tuple)):
                                continue
                        except Exception:
                            continue
                    elif line.operator in ['=', '!=', '>', '<', '>=', '<=']:
                        if field_type == 'integer':
                            if not str(val).isdigit() or '.' in str(val):
                                continue
                            val = int(val)
                        elif field_type == 'float':
                            try:
                                val = float(val)
                            except ValueError:
                                continue
                        elif field_type == 'date':
                            val = Date.to_date(val)
                        elif field_type == 'datetime':
                            val = Datetime.to_datetime(val)
                    elif line.operator == 'set':
                        domain.append((domain_key, '!=', False))
                        continue
                    elif line.operator == 'not set':
                        domain.append((domain_key, '=', False))
                        continue

                    domain.append((domain_key, line.operator, val))

                except Exception as e:
                    print(f"⚠️ web_search_read rule skipped: {e}")
                    continue

        records = self.search_read(domain, fields, offset=offset, limit=limit, order=order)
        if not records:
            return {
                'length': 0,
                'records': []
            }

        current_length = len(records) + offset
        limit_reached = len(records) == limit
        force_search_count = self._context.get('force_search_count')
        count_limit_reached = count_limit and count_limit <= current_length
        if limit and ((limit_reached and not count_limit_reached) or force_search_count):
            length = self.search_count(domain, limit=count_limit)
        else:
            length = current_length

        return {
            'length': length,
            'records': records
        }
