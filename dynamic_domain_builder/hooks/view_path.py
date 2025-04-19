from odoo.models import BaseModel
from odoo.tools.safe_eval import safe_eval
from odoo import api
from odoo.exceptions import ValidationError
from odoo.fields import Date, Datetime
from odoo import api
from odoo.osv import expression
from odoo.tools import date_utils

from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


original_name_search = BaseModel.name_search  # backup



@api.model
@api.readonly
def name_search(self, name='', args=None, operator='ilike', limit=100) -> list[tuple[int, str]]:
    args = args or []

    # 🧠 Rule logic: Prefer user-specific rules
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
                related_type = line.related_field_id.ttype if line.related_field_id else 'integer'

                if line.operator in ['in', 'not in']:
                    val = safe_eval(val)
                    if not isinstance(val, list):
                        continue
                    # Optional: filter for integer-only values
                    if related_type == 'integer' and not all(str(v).isdigit() for v in val):
                        continue
                elif line.operator in ['=', '!=', '>', '<', '>=', '<=']:
                    if domain_key == 'id':
                        if not str(val).isdigit():
                            continue
                        val = int(val)
                    elif related_type == 'date':
                        val = Date.to_date(val)
                    elif related_type == 'datetime':
                        val = Datetime.to_datetime(val)
                    elif related_type == 'integer':
                        if not str(val).isdigit():
                            continue
                        val = int(val)
                elif line.operator == 'set':
                    args.append((domain_key, '!=', False))
                    continue
                elif line.operator == 'not set':
                    args.append((domain_key, '=', False))
                    continue

                args.append((domain_key, line.operator, val))
        except Exception as e:
            _logger.warning("⚠️ name_search rule skipped: %s", e)
            continue

    # Combine with default name search logic
    domain = expression.AND([[('display_name', operator, name)], args])
    records = self.search_fetch(domain, ['display_name'], limit=limit)
    return [(record.id, record.display_name) for record in records.sudo()]

# ✅ Inject globally (Odoo-wide patch)
BaseModel.name_search = name_search
