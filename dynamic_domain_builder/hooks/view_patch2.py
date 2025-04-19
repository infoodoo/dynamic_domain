from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from lxml import etree
from odoo.exceptions import ValidationError
from collections import defaultdict
from odoo.fields import Date, Datetime


class Base(models.AbstractModel):
    _inherit = 'base'


    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        domain = domain or []
        is_from_search_more = self.env.context.get("is_from_search_more")

        if not is_from_search_more:
            return super().web_search_read(domain, specification, offset, limit, order, count_limit)

        # ✅ Domain rules logic
        rules = self.env['field.domain.rule.line'].search([
            ('field_name.relation', '=', self._name),
            ('rule_id.active', '=', True),
            ('rule_id.user_id', '=', self.env.uid),
        ]) or self.env['field.domain.rule.line'].search([
            ('field_name.relation', '=', self._name),
            ('rule_id.active', '=', True),
            ('rule_id.user_id', '=', False),
        ])

        for line in rules:
            try:
                field = line.field_name
                val = line.value

                if field.ttype in ['many2one', 'many2many'] and field.relation == self._name:
                    domain_key = line.related_field_id.name if line.related_field_id else 'id'

                    if line.operator in ['in', 'not in']:
                        val = safe_eval(val)
                        if not isinstance(val, list):
                            continue

                    elif line.operator in ['=', '!=', '>', '<', '>=', '<=']:
                        if domain_key == 'id':
                            if not str(val).isdigit():
                                continue
                            val = int(val)
                        elif line.related_field_id:
                            ttype = line.related_field_id.ttype
                            if ttype == 'date':
                                val = Date.to_date(val)
                            elif ttype == 'datetime':
                                if line.operator == '>':
                                    val = Datetime.to_datetime(val + " 23:59:59")
                                elif line.operator == '>=':
                                    val = Datetime.to_datetime(val + " 00:00:00")
                                elif line.operator == '<':
                                    val = Datetime.to_datetime(val + " 00:00:00")
                                elif line.operator == '<=':
                                    val = Datetime.to_datetime(val + " 23:59:59")
                                else:
                                    val = Datetime.to_datetime(val)
                            elif ttype in ['integer', 'float']:
                                if ttype == 'integer':
                                    if not str(val).isdigit() or '.' in str(val):
                                        continue  # prevent float strings from slipping in
                                    val = int(val)
                                elif ttype == 'float':
                                    try:
                                        val = float(val)
                                    except ValueError:
                                        continue

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

        records = self.search_fetch(domain, specification.keys(), offset=offset, limit=limit, order=order)
        values_records = records.web_read(specification)
        return self._format_web_search_read_results(domain, values_records, offset, limit, count_limit)
