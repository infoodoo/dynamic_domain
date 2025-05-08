from odoo.models import BaseModel
from odoo.tools.safe_eval import safe_eval
from odoo import api
from odoo.exceptions import ValidationError
from odoo.fields import Date, Datetime
from datetime import datetime


original_name_search = BaseModel.name_search  # backup


@api.model
def patched_name_search(self, name='', args=None, operator='ilike', limit=100):
    args = args or []

    # 1. Prefer user-specific rules
    rules = self.env['field.domain.rule.line'].sudo().search([
        ('field_name.relation', '=', self._name),
        ('rule_id.active', '=', True),
        ('rule_id.user_id', '=', self.env.uid),
    ])

    # 2. Fallback to global rules
    if not rules:
        rules = self.env['field.domain.rule.line'].sudo().search([
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
                            if line.operator in ['>']:
                                val = Datetime.to_datetime(val + " 23:59:59")
                            elif line.operator in ['>=']:
                                val = Datetime.to_datetime(val + " 00:00:00")
                            elif line.operator in ['<']:
                                val = Datetime.to_datetime(val + " 00:00:00")
                            elif line.operator in ['<=']:
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
                    args.append((domain_key, '!=', False))
                    continue
                elif line.operator == 'not set':
                    args.append((domain_key, '=', False))
                    continue
                print(domain_key)

                args.append((domain_key, line.operator, val))

        except Exception as e:
            print(f"⚠️ Rule skipped: {e}")
            continue

    ids = self._name_search(name, args, operator, limit=limit)

    # 🔧 Future-proof way to avoid name_get() deprecation
    try:
        return [(rec.id, rec.display_name) for rec in self.browse(ids).sudo()]
    except Exception:
        return self.browse(ids).sudo().name_get()


# ✅ Inject globally (Odoo-wide patch)
BaseModel.name_search = patched_name_search
