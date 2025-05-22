from odoo import models, fields, api, exceptions


class TravelMgmtLine(models.Model):
    _name = "travel.mgmt.line"
    _description = "Travel Management Line"
    _order = "date desc"

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain=[("can_be_expensed", "=", True)],
        required=True,
        ondelete="cascade",  # Impostazione per eliminare la linea se il prodotto viene eliminato
    )
    quantity = fields.Float(string="Quantity", required=True)
    price_unit = fields.Float(
        string="Unit Price",
        related="product_id.standard_price",
        readonly=False,  # Impostato su False per permettere la modifica manuale, se necessario
    )
    date = fields.Date(string="Date", default=fields.Date.context_today)
    travel_id = fields.Many2one("travel.mgmt", string="Travel", ondelete="cascade")

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="travel_id.currency_id",
        store=True,
        readonly=True,
    )

    total = fields.Monetary(
        string="Total",
        compute="_compute_total",
        store=True,
        currency_field="currency_id",
    )

    @api.depends("quantity", "price_unit")
    def _compute_total(self):
        for line in self:
            line.total = line.quantity * line.price_unit

    @api.constrains("quantity")
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise exceptions.UserError("Quantity must be greater than zero.")

    @api.constrains("price_unit")
    def _check_price_unit(self):
        for line in self:
            if line.price_unit <= 0:
                raise exceptions.UserError("Unit price must be greater than zero.")

    @api.constrains("product_id")
    def _check_product_price(self):
        for line in self:
            if not line.product_id.standard_price:
                raise exceptions.UserError(
                    "The selected product must have a valid unit price."
                )
