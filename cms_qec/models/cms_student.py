# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import date


class CMSStudent(models.Model):
    _name = 'cms.student'
    _description = 'Student Information'


    name = fields.Char('Student Name', required=True)
    father_name = fields.Char('Father Name', required=True)
    registration_no = fields.Char(string='Registration No.', required=True)
    cnic = fields.Char(string='Student CNIC')
    contact_phone = fields.Char('Phone no.')
    contact_mobile = fields.Char('Mobile no')
    image = fields.Binary('image')
    admission_date = fields.Date('Admission Date', default=date.today())
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender', states={'done': [('readonly', True)]}, required=True)
    user_id = fields.Many2one('res.users', string='Responsible', readonly=True, default=lambda self: self.env.user)
    date_of_birth = fields.Date('Date of Birth', required=True)
    age = fields.Integer(compute='_compute_student_age', string='Age', readonly=True)
    
    remark = fields.Text('Remark', states={'done': [('readonly', True)]})
    
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancelled', 'Cancelled')], 
                             'Status', readonly=True, default="draft")
    
    active = fields.Boolean(default=True)
        
    
    @api.depends('date_of_birth')
    def _compute_student_age(self):
        '''Method to calculate student age'''
        current_date = date.today()
        for rec in self:
            if rec.date_of_birth:
                start = rec.date_of_birth
                age = (current_date - start).days / 365
                # Age should be greater than 0
                if age > 0.0:
                    rec.age = age
                else:
                    rec.age = 0
            else:
                rec.age = 0
                

    def set_done(self):
        '''Method to change state to done'''
        self.state = 'done'

    def set_cancel(self):
        '''Set the state to draft'''
        self.state = 'cancelled'

