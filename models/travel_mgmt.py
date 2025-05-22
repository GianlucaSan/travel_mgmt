from odoo import models, fields, api, exceptions


class TravelMgmt(models.Model):
    _name = "travel.mgmt"
    _description = "Travel Management"

    name = fields.Char(string="Nome viaggio")
    date_from = fields.Date(string="Data Inizio")
    date_to = fields.Date(string="Data Fine")
    employee_id = fields.Many2one(
        "hr.employee",
        string="Dipendente",
        default=lambda self: self.env.user.employee_id,
    )
    company_id = fields.Many2one(
        "res.company", string="Azienda", default=lambda self: self.env.company
    )
    notes = fields.Text(string="Note")
    paid_by = fields.Selection(
        [("employee", "Dipendente"), ("company", "Azienda")], string="Pagato da"
    )
    state = fields.Selection(
        [("draft", "Bozza"), ("expenses_created", "Spese Create")],
        string="Status",
        default="draft",
    )
    expense_lines = fields.One2many(
        "travel.mgmt.line", "travel_id", string="Expense Lines"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise exceptions.UserError("Data Da deve essere minore di Data A")

    @api.model
    def write(self, vals):
        if "state" in vals and self.state == "expenses_created":
            raise exceptions.UserError(
                "Non puoi modificare lo stato dopo che le spese sono state create."
            )
        return super(TravelMgmt, self).write(vals)

    def action_create_expenses(self):
        for rec in self:
            for line in rec.expense_lines:
                # Crea la nota spese e assegna il campo currency_id
                self.env["hr.expense"].create(
                    {
                        "name": rec.name,
                        "employee_id": rec.employee_id.id,
                        "company_id": rec.company_id.id,
                        "payment_mode": rec.paid_by,
                        "date": line.date,
                        "unit_amount": line.price_unit,
                        "quantity": line.quantity,
                        "product_id": line.product_id.id,
                        "currency_id": rec.currency_id.id,  # Imposta la valuta
                    }
                )
            # Imposta lo stato del viaggio come "Spese Create"
            rec.state = "expenses_created"

        return True
