from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from lxml import etree
from odoo.exceptions import ValidationError
from collections import defaultdict



class FieldDomainRule(models.Model):
    _name = 'field.domain.rule'
    _description = 'Custom Domain Rule for Form Field'

    name = fields.Char("Rule Name", required=True)

    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=False,
        ondelete='set null',
    )
    rule_line_ids = fields.One2many('field.domain.rule.line', 'rule_id', string="Conditions")

    user_id = fields.Many2one("res.users", string="User")
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals):
        model_id = vals.get('model_id')
        user_id = vals.get('user_id') or False

        domain = [('model_id', '=', model_id), ('user_id', '=', user_id)]
        if self.search_count(domain):
            raise ValidationError("A rule for this model and user already exists.")
        return super().create(vals)

    def write(self, vals):
        for rec in self:
            model_id = vals.get('model_id', rec.model_id.id)
            user_id = vals.get('user_id', rec.user_id.id if rec.user_id else False)

            domain = [
                ('model_id', '=', model_id),
                ('user_id', '=', user_id),
                ('id', '!=', rec.id)  # exclude self to avoid false positive
            ]

            if self.search_count(domain):
                raise ValidationError("A rule for this model and user already exists.")

        return super().write(vals)


class FieldDomainRuleLine(models.Model):
    _name = 'field.domain.rule.line'
    _description = 'One rule condition for a field'

    rule_id = fields.Many2one('field.domain.rule', required=True, ondelete='cascade')
    field_name = fields.Many2one(
        'ir.model.fields',
        string='Field',
        domain="[('model_id', '=', parent.model_id),('ttype', 'in', ['many2one', 'many2many'])]",
        required=False,
        ondelete='set null'
    )
    related_field_id = fields.Many2one('ir.model.fields', string="Related Field")
    related_domain = fields.Json(compute='_compute_related_domain', store=False)

    operator = fields.Selection([
        ('=', '='), ('!=', '!='), ('in', 'is in'), ('not in', 'is not in'),
        ('ilike', 'contains'), ('not ilike', 'does not contain'),
        ('set', 'is set'), ('not set', 'is not set'),
        ('>', '>'), ('<', '<'),
        ('>=', '>='), ('<=', '<='),
    ], required=True)
    value = fields.Char("Value")

    @api.depends('field_name')
    @api.onchange('field_name')
    def _compute_related_domain(self):
        for rec in self:
            rec.related_domain = []
            if rec.field_name and rec.field_name.ttype in ['many2one', 'many2many'] and rec.field_name.relation:
                related_model = self.env['ir.model'].search([('model', '=', rec.field_name.relation)], limit=1)
                if related_model:
                    rec.related_domain = [('model_id', '=', related_model.id),('ttype', 'not in', ['many2one', 'many2many', 'one2many'])]

