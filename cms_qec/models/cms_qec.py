from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError, ValidationError

class cms_qec_question_area(models.Model):
    
    _name = "cms.qec.question.area"
    _descpription = "QEC Question Area"

    name = fields.char('Question Area', size=300, required=True)
    questions = fields.one2many('cms.qec.question','question_area', 'Questions')       
        

#
class cms_qec_question(models.Model):
    
    _name= "cms.qec.question"
    _descpription = "QEC Question"

    name= fields.text('Question', size=300, required=True)
    question_no= fields.integer('Question No', required=True)
    response_type= fields.selection([('Rating','Rating'),('Boolean','Boolean'),('Text','Text')],'Response Type', required=True)
    question_area= fields.many2one('cms.qec.question.area', 'Question Area', required=True)
    options= fields.one2many('cms.qec.option','qec_question', 'Options')       
    
    _defaults = {
        'response_type': lambda *a: 'Rating',
        }


class cms_qec_option_label(models.Model):
    
    _name= "cms.qec.option.label"
    _descpription = "QEC Option Label"

    name = fields.char('Name', size=200, required=True)
        



class cms_qec_option(models.Model):
    
    def _set_name(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids, context)
        for f in records:
            result[f.id] = str(f.label.name)
        return result
    
    _name = "cms.qec.option"
    _descpription = "QEC Option"

    name= fields.function(_set_name, method=True, string='Name', type='char', size=300)
    label= fields.many2one('cms.qec.option.label', 'Label', required=True)
    sequence= fields.integer('Option Sequence', required=True)
    value= fields.integer('Value', required=True)
    state= fields.selection([('Active','Active'),('Inactive','Inactive')],'State', required=True)
    qec_question: fields.many2one('cms.qec.question', 'Question', required=True)

    
    _defaults = {
        'state': lambda *a: 'Active',
    }
    


class cms_qec_template(models.Model):
    
    _name= "cms.qec.template"
    _descpription = "QEC Template"

    name = fields.char('Name', size=200, required=True),
    evaluation_for = fields.selection([('Employee','Employee'),('Student','Student'),('Subject','Subject'),('General','General')],'Evaluation For', required=True)
    template_lines = fields.one2many('cms.qec.template.lines','qec_template', 'Template Lines')
    template_areas = fields.one2many('cms.qec.template.area','qec_template', 'Template Area')
    state = fields.selection([('Draft','Draft'),('Active','Active'),('Inactive','Inactive'),('Cancelled','Cancelled')],'State', required=True)


class cms_qec_template_lines(models.Model):
    
    _name= "cms.qec.template.lines"
    _descpription = "QEC Template Lines"

    name= fields.many2one('cms.qec.question', 'Question', required=True),
    qec_template= fields.many2one('cms.qec.template', 'Template', required=True),
    serial_no= fields.integer('Serial No', required=True),
    statistical_effect=fields.boolean('Statistical Effect', required=True),
    question_area= fields.related('name', 'question_area', 'name', string='Question Area',size=30, type='char', readonly=True),

    
    _sql_constraints = [
        ('unique_template_question', 'unique (qec_template,name)', 'Question must be unique for a template!'),
        ('unique_template_sequence', 'unique (qec_template,serial_no)', 'Sequence must be unique for a template!')]
    
    _defaults = {
        'statistical_effect': lambda *a: True,
    }
    
cms_qec_template_lines()

class cms_qec_template_area(models.Model):
    
    _name= "cms.qec.template.area"
    _descpription = "QEC Template Area"

    name=fields.many2one('cms.qec.question.area', 'Area', required=True)
    qec_template= fields.many2one('cms.qec.template', 'Template', required=True)
    serial_no= fields.integer('Serial No', required=True)

    
    _sql_constraints = [
        ('unique_template_question_area', 'unique (qec_template,name)', 'Question Area must be unique for a template!'),
        ('unique_template_area_sequence', 'unique (qec_template,serial_no)', 'Area Sequence must be unique for a template!')]
    


class cms_qec_evaluation(models.Model):
    
    def _set_name(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids, context)
        for f in records:
            _date = datetime.datetime.strptime(str(f.evaluation_date), '%Y-%m-%d').strftime('%A, %d %b %Y')
            result[f.id] = str(f.qec_template.name) + ": " + str(_date)
        return result
    
    def draft_qec_evaluation(self, cr, uid, ids):
        
        self.write(cr, uid, ids, { 'state' : 'Draft' })
        return True

    def start_qec_evaluation(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state' : 'Started' })        
        return True

    def approve_qec_evaluation(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state' : 'Approved' })        
        return True

    def close_qec_evaluation(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state' : 'Closed' })
        return True

    def cancel_qec_evaluation(self, cr, uid, ids):
        self.write(cr, uid, ids, { 'state' : 'Cancelled' })
        return True
    
    def _get_qec_questions(self, cr, uid):
    
        parent_dict = {'response_id':'','response':[]}
        qec_questions_list = []

        sql = """select cms_qec_evaluation.id, serial_no, cms_qec_question.id as question_id, cms_qec_question.name as question_text, 
            cms_qec_option.id as option_id, cms_qec_option_label.name as option_label, cms_qec_question.response_type as question_response_type,
            cms_qec_template.evaluation_for
            from cms_qec_evaluation
            inner join cms_qec_template
            on cms_qec_template.id = cms_qec_evaluation.qec_template
            inner join cms_qec_template_lines
            on cms_qec_template.id = cms_qec_template_lines.qec_template
            inner join cms_qec_question
            on cms_qec_question.id = cms_qec_template_lines.name
            inner join cms_qec_option
            on cms_qec_question.id = cms_qec_option.qec_question
            inner join cms_qec_option_label
            on cms_qec_option_label.id = cms_qec_option.label
            where cms_qec_evaluation.state = 'Started' 
            order by cms_qec_template_lines.serial_no, cms_qec_option.sequence"""
        
        cr.execute(sql)
        rows = cr.fetchall()
        
        for row in rows:
            
            mydict = {'qec_id':row[0],'serial_no':row[1],'question_id':row[2],'question_text':row[3], 'option_id':row[4], 'option_label':row[5], 'question_response_type':row[6], 'evaluation_for':row[7]}
            qec_questions_list.append(mydict)
            
        logger.notifyChannel('QEC-Question-List - '+'uid:'+str(uid), netsvc.LOG_INFO,'** _get_qec_questions() Method is called, ' + str(len(rows)) + "records are returned")
        
        parent_dict['response'] = qec_questions_list 
        return parent_dict
    
    def _get_qec_student_subjects(self, cr, uid, student_no):
    
        parent_dict = {'response_id':'','response':[]}
        student_subject_list = []

        now = datetime.datetime.now()
        sql = """select cms_timetable.id, 
            (select name from cms_subject where id = calculated_subject) as subject,
            (select name from hr_employee where id = teacher) as teacher
            from cms_studentregislines 
            inner join cms_timetable
            on cms_timetable.id = cms_studentregislines.subject
            inner join cms_academiccalender
            on cms_academiccalender.id = cms_timetable.semester
            inner join cms_studentregis
            on cms_studentregis.id = cms_studentregislines.semester
            where cms_studentregis.student = (select id from cms_entryregis where cadidate_no = '""" + str(student_no) + """')
            AND subject_status = 'Current'
            AND '""" + str(now) + """' between semeser_start_date and semester_end_date"""
        
        cr.execute(sql)
        rows = cr.fetchall()
        
        for row in rows:
            
            mydict = {'subject_id':row[0],'subject_name':row[1],'teacher_name':row[2]}
            student_subject_list.append(mydict)
            
        logger.notifyChannel('QEC-Student-Subject-List - '+'uid:'+str(uid), netsvc.LOG_INFO,'** _get_qec_student_subjects() Method is called, ' + str(len(rows)) + " records are returned")
        
        parent_dict['response'] = student_subject_list 
        return parent_dict
    
    def _submit_qec_survey(self, cr, uid, feedbacks):
        evaluation_table = self.pool.get('cms.qec.evaluation')
        evaluation_feedbacck_table = self.pool.get('cms.qec.evaluation.feedbacck')
        evaluation_feedbacck_table_line = self.pool.get('cms.qec.evaluation.feedbacck.lines')
        
        # Use this for Testing this Service (For testing I have already call this method from write method of cms_city(), uncomment there)
        #feedbacks = [{'SubmissionDateTime': '2020-12-21 21:41:28', 'FeedBackLines': 
        #    [{'SerialNo': 1, 'OptionText': 'A', 'OptionID': 1, 'QuestionID': 1}, 
        #    {'SerialNo': 2, 'OptionText': 'B', 'OptionID': 2, 'QuestionID': 2}, 
        #    {'SerialNo': 3, 'OptionText': 'C', 'OptionID': 3, 'QuestionID': 3}, 
        #    {'SerialNo': 4, 'OptionText': 'D', 'OptionID': 4, 'QuestionID': 4}, 
        #    {'SerialNo': 5, 'OptionText': 'E', 'OptionID': 5, 'QuestionID': 5}, 
        #    {'SerialNo': 6, 'OptionText': 'F', 'OptionID': 1, 'QuestionID': 6}, 
        #    {'SerialNo': 7, 'OptionText': 'BaharAli', 'OptionID': 2, 'QuestionID': 7}], 
        #    'CandidateNo': '191301777', 'QEC_ID': 15, 'Student': '', 'Employee': '', 'Subject': '8021'}]

        i = 1
        feedback_list = []
        for feedback in feedbacks:
            evaluation_id = feedback['QEC_ID']
            candidate_no  = feedback['CandidateNo']
            completion_date  = feedback['SubmissionDateTime']

            timetable = None
            student = None
            employee = None
            if str(feedback['Subject']).strip() != '':
                timetable  = feedback['Subject']
            if str(feedback['Student']).strip() != '':
                student  = feedback['Student']
            if str(feedback['Employee']).strip() != '':
                employee  = feedback['Employee']
            
            evaluation_obj = evaluation_table.browse(cr, uid, evaluation_id)
            template_id = evaluation_obj.qec_template.id
            
            evaluation_feedbacck_lines = []
            for feedback_line in feedback['FeedBackLines']:
                serial_no  = feedback_line['SerialNo']
                evaluation_feedbacck_lines.append((0,0, {'serial_no':serial_no, 'question':feedback_line['QuestionID'], 'option':feedback_line['OptionID'], 'text':feedback_line['OptionText']}))

            #eva_exist_ids = evaluation_feedbacck_table.search(cr,uid,[('feedback_token','=', str(candidate_no)), ('timetable','=', timetable),
            #                                                        ('qec_template','=', template_id),('qec_evaluation','=', evaluation_id)])
            
            sql = """select id from cms_qec_evaluation_feedbacck
                where feedback_token = '""" + str(candidate_no) + """'
                AND timetable = """ + str(timetable) + """
                AND qec_template = """ + str(template_id) + """
                AND qec_evaluation = """ + str(evaluation_id)
                
            cr.execute(sql)
            eva_exist_ids = cr.fetchone()

            if eva_exist_ids:
                evaluation_feedbacck_id = eva_exist_ids[0]
                evaluation_feedbacck_table.write(cr,uid, eva_exist_ids[0], {'feedback_token':str(candidate_no),
                    'evaluation_for':'Subject','student':student, 'employee':employee,'timetable':timetable,'qec_template':template_id,
                    'state':'Completed','completed_date':completion_date, 'completed_by':272,'reopen_date':None, 'reopen_by':None,
                    'recomplete_date':None,'recomplete_by':None, 'qec_evaluation':evaluation_id, 
                    #'sequence_no':None, 'ref_teacher':None
                    })
                
                for feedback_line in feedback['FeedBackLines']:
                    eva_line_exist_ids = evaluation_feedbacck_table_line.search(cr,uid,[('name','=', eva_exist_ids[0]), 
                                                ('question','=', feedback_line['QuestionID'])])
                    if eva_line_exist_ids:
                        evaluation_feedbacck_table_line.write(cr, uid, eva_line_exist_ids[0], {'serial_no':feedback_line['SerialNo'], 
                                                                'question':feedback_line['QuestionID'], 'option':feedback_line['OptionID'], 
                                                                'text':feedback_line['OptionText']})
                    else:
                        evaluation_feedbacck_table_line.create(cr, uid, eva_line_exist_ids[0], {'serial_no':feedback_line['SerialNo'], 
                                                                'question':feedback_line['QuestionID'], 'option':feedback_line['OptionID'], 
                                                                'text':feedback_line['OptionText']})
            else:
                evaluation_feedbacck_id = evaluation_feedbacck_table.create(cr,uid,{'feedback_token':str(candidate_no),
                    'evaluation_for':'Subject','student':student, 'employee':employee,'timetable':timetable,'qec_template':template_id,
                    'state':'Completed','completed_date':completion_date, 'completed_by':272,'reopen_date':None, 'reopen_by':None,
                    'recomplete_date':None,'recomplete_by':None, 'qec_evaluation':evaluation_id, 
                    #'sequence_no':None, 'ref_teacher':None, 
                    'evaluation_feedbacck_lines':evaluation_feedbacck_lines})
            
            logger.notifyChannel("Records: " + str(i) + " Out of ", netsvc.LOG_INFO, str(len(feedbacks)))
            
            if evaluation_feedbacck_id:
                evalauation_feedback_obj = evaluation_feedbacck_table.browse(cr, uid, evaluation_feedbacck_id)
                feedback_list.append({'qec_evaluation':evalauation_feedback_obj.qec_evaluation.id, 
                                      'feedback_token':evalauation_feedback_obj.feedback_token,
                                      'subject':evalauation_feedback_obj.timetable.id if evalauation_feedback_obj.timetable else 0,
                                      'student':evalauation_feedback_obj.student.id if evalauation_feedback_obj.student else 0,
                                      'employee':evalauation_feedback_obj.employee.id if evalauation_feedback_obj.employee else 0})
            i = i + 1

        return {'response_id':1,'response':feedback_list}
    
    def _import_qec_evaluations_data(self, cr, uid):
        sql = """SELECT var00, var01, var02, var03, var04, var05, var06, var07, var08, var09, var10,
                var11, var12, var13, var14, var15, var16, var17, var18, var19, var20,
                var21, var22, var23, var24, var25, var26, var27, var28, var29, var30,
                sequence_no as rec_31, total, total_subject, student, state, ref_teacher,
                enter_at as rec_37, enter_by, reopen_at, reopen_by, recomplete_at, recomplete_by,
                search_record as rec_43, search_group_subject, search_teacher, search_semester, search_program, 
                feedback_token as rec_48, feedback_entered_by, student_comments, name,
                to_char(create_date , 'YYYY-MM-DD') as create_date_52, id as qec_id
                FROM cms_qec 
                where is_migrated = false
                and search_teacher not like 'Dummy Teacher'
                and search_teacher is not null 
                order by create_date"""
    
        cr.execute(sql)
        qec_rows = cr.fetchall()
        
        i = 0
        option_table = self.pool.get('cms.qec.option')
        evaluation_feedback_table = self.pool.get('cms.qec_evaluation_feedback')
        #evaluation_table = self.pool.get('cms.qec.evaluation')
        evaluation_feedbacck_table = self.pool.get('cms.qec.evaluation.feedbacck')
#         prev_date = None
#         evaluation_id = None
        
        
        for qec_row in qec_rows:
            evalauation_feedback_ids = evaluation_feedback_table.search(cr, uid, [('feedback_token', '=', qec_row[48])])
            evalauation_feedback_obj = evaluation_feedback_table.browse(cr, uid, evalauation_feedback_ids[0])
            evaluation_id = evalauation_feedback_obj.qec_evaluation.id
            logger.notifyChannel('Evaluation ID: ', netsvc.LOG_INFO, str(evaluation_id))
        
            i = i + 1
            
#             if evaluation_id == None:
#                 evaluation_id = evaluation_table.create(cr,uid,{'evaluation_date':qec_row[52],'qec_template':2,'state':'Draft'})
#                 prev_date = qec_row[52]
                
#             date_format = "%Y-%m-%d"
#             date_1 = datetime.datetime.strptime(prev_date, date_format)
#             date_2 = datetime.datetime.strptime(qec_row[52], date_format)
#             delta = date_2 - date_1
            
            logger.notifyChannel("Records: " + str(i) + " Out of ", netsvc.LOG_INFO, str(len(qec_rows)))
        
#             if delta.days > 120:
#                 evaluation_id = evaluation_table.create(cr,uid,{'evaluation_date':qec_row[52],'qec_template':2,'state':'Draft'})
#                 logger.notifyChannel('Evaluation ID: ', netsvc.LOG_INFO, str(evaluation_id))
#                 prev_date = qec_row[52]
            
            evaluation_feedbacck_lines = []
            off_set = 0
            if qec_row[0]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':0, 'question':32 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 32 + off_set),('value', '=', qec_row[0])])[0], 'text':''}))
            if qec_row[50]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':29, 'question':31 + off_set, 'option':'', 'text':qec_row[50]}))
            
            if qec_row[1]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':1, 'question':1 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 1 + off_set),('value', '=', qec_row[1])])[0], 'text':''}))
            if qec_row[2]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':2, 'question':2 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 2 + off_set),('value', '=', qec_row[2])])[0], 'text':''}))
            if qec_row[3]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':3, 'question':3 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 3 + off_set),('value', '=', qec_row[3])])[0], 'text':''}))
            if qec_row[4]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':4, 'question':4 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 4 + off_set),('value', '=', qec_row[4])])[0], 'text':''}))
            if qec_row[5]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':5, 'question':5 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 5 + off_set),('value', '=', qec_row[5])])[0], 'text':''}))
            if qec_row[6]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':6, 'question':6 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 6 + off_set),('value', '=', qec_row[6])])[0], 'text':''}))
            if qec_row[7]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':7, 'question':7 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 7 + off_set),('value', '=', qec_row[7])])[0], 'text':''}))
            if qec_row[8]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':8, 'question':8 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 8 + off_set),('value', '=', qec_row[8])])[0], 'text':''}))
            if qec_row[9]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':9, 'question':9 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 9 + off_set),('value', '=', qec_row[9])])[0], 'text':''}))
            if qec_row[10]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':10, 'question':10 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 10 + off_set),('value', '=', qec_row[10])])[0], 'text':''}))
            if qec_row[11]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':11, 'question':11 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 11 + off_set),('value', '=', qec_row[11])])[0], 'text':''}))
            if qec_row[12]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':12, 'question':12 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 12 + off_set),('value', '=', qec_row[12])])[0], 'text':''}))
            if qec_row[13]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':13, 'question':13 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 13 + off_set),('value', '=', qec_row[13])])[0], 'text':''}))
            if qec_row[14]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':14, 'question':14 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 14 + off_set),('value', '=', qec_row[14])])[0], 'text':''}))
            #if qec_row[15]:
                #evaluation_feedbacck_lines.append((0,0, {'serial_no':15, 'question':16 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 15 + off_set),('value', '=', qec_row[15])])[0], 'text':''}))
            if qec_row[16]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':15, 'question':16 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 16 + off_set),('value', '=', qec_row[16])])[0], 'text':''}))
            #if qec_row[17]:
                #evaluation_feedbacck_lines.append((0,0, {'serial_no':17, 'question':19 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 17 + off_set),('value', '=', qec_row[17])])[0], 'text':''}))
            if qec_row[18]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':16, 'question':18 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 18 + off_set),('value', '=', qec_row[18])])[0], 'text':''}))
            if qec_row[19]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':17, 'question':19 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 19 + off_set),('value', '=', qec_row[19])])[0], 'text':''}))
            if qec_row[20]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':18, 'question':20 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 20 + off_set),('value', '=', qec_row[20])])[0], 'text':''}))
            if qec_row[21]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':19, 'question':21 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 21 + off_set),('value', '=', qec_row[21])])[0], 'text':''}))
            if qec_row[22]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':20, 'question':22 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 22 + off_set),('value', '=', qec_row[22])])[0], 'text':''}))
            if qec_row[23]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':21, 'question':23 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 23 + off_set),('value', '=', qec_row[23])])[0], 'text':''}))
            if qec_row[24]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':22, 'question':24 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 24 + off_set),('value', '=', qec_row[24])])[0], 'text':''}))
            if qec_row[25]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':23, 'question':25 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 25 + off_set),('value', '=', qec_row[25])])[0], 'text':''}))
            if qec_row[26]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':24, 'question':26 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 26 + off_set),('value', '=', qec_row[26])])[0], 'text':''}))
            if qec_row[27]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':25, 'question':27 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 27 + off_set),('value', '=', qec_row[27])])[0], 'text':''}))
            if qec_row[28]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':26, 'question':28 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 28 + off_set),('value', '=', qec_row[28])])[0], 'text':''}))
            if qec_row[29]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':27, 'question':29 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 29 + off_set),('value', '=', qec_row[29])])[0], 'text':''}))
            if qec_row[30]:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':28, 'question':30 + off_set, 'option':option_table.search(cr, uid, [('qec_question', '=', 30 + off_set),('value', '=', qec_row[30])])[0], 'text':''}))
            
            state = str(qec_row[35])
            evaluation_feedbacck_table.create(cr,uid,{'feedback_token':qec_row[48],'evaluation_for':'Subject','student':'',
                'employee':'','timetable':qec_row[51],'qec_template':1,'evaluation_feedbacck_lines':evaluation_feedbacck_lines,
                'state':state.capitalize(),'completed_date':qec_row[37],'completed_by':qec_row[38],'reopen_date':qec_row[39],
                'reopen_by':qec_row[40],'recomplete_date':qec_row[41],'recomplete_by':qec_row[42],'qec_evaluation':evaluation_id,
                #'sequence_no':qec_row[31],'ref_teacher':qec_row[36]
                })
            
            self.pool.get('cms.qec').write(cr,uid, qec_row[53], {'is_migrated':True})
            
        
        return True
    
    _name = "cms.qec.evaluation"
    _descpription = "QEC Evaluation"

    name= fields.function(_set_name, method=True, string='Name', type='char', size=300)
    evaluation_for= fields.related('qec_template', 'evaluation_for', string='Evaluation For',size=30, type='char', readonly=True)
    evaluation_date= fields.date('Evaluation Date', required=True)
    
    qec_template= fields.many2one('cms.qec.template', 'Questions Template', required=True)
    evaluation_feedbacks= fields.one2many('cms.qec.evaluation.feedbacck','qec_evaluation', 'Evaluation Feedbacks')
    state= fields.selection([('Draft','Draft'),('Started','Started'),('Approved','Approved'),('Closed','Closed'),('Cancelled','Cancelled')],'State', required=True)
    
    closed_by= fields.many2one('res.users', 'Closed By')
    closed_date= fields.date('Closed Date')
    
    started_by=fields.many2one('res.users', 'Started By')
    started_date= fields.date('Started Date')
    
    cancelled_by= fields.many2one('res.users', 'Cancelled By')
    cancelled_date= fields.date('Cancelled Date')
    
    _defaults = {
        'evaluation_for': lambda *a: '',
        'state': lambda *a: 'Draft',
    }
    


class cms_qec_evaluation_feedbacck(models.Model):
    
    def _invalidate_feedback_duplicate_entries(self, cr, uid):
        
        ########################### Checking Invalid Entries at Feedback and respective Feedback Lines' Level #######################
        sql = """select feedback_token, timetable, concat('(', array_to_string(array_agg(cms_qec_evaluation_feedbacck.id),','), ')') 
            from cms_qec_evaluation_feedbacck
            where feedback_token is not null
            and is_valid = True
            group by feedback_token, timetable
            having count(cms_qec_evaluation_feedbacck.id)  > 1"""
    
        cr.execute(sql)
        qec_rows = cr.fetchall()
        
        logger.notifyChannel("Records Corrected (cms_qec_evaluation_feedbacck): ", netsvc.LOG_INFO, str(len(qec_rows)))
        
        for qec_row in qec_rows:
            sql = """select id from cms_qec_evaluation_feedbacck
                where id in """ + str(qec_row[2]) + """
                order by id"""
    
            cr.execute(sql)
            rows = cr.fetchall()
            
            i = 1
            for row in rows:
                if i == 1:
                    i += 1
                    continue
                sql = """UPDATE cms_qec_evaluation_feedbacck set is_valid = False
                    WHERE id = """ + str(row[0])
    
                cr.execute(sql)
                cr.commit()

                sql = """UPDATE cms_qec_evaluation_feedbacck_lines set is_valid = False
                    WHERE name = """ + str(row[0])
    
                cr.execute(sql)
                cr.commit()
        
        ########################### Checking Invalid Entries at Feedback Lines' Level #######################
        sql = """select name, question, concat('(', array_to_string(array_agg(cms_qec_evaluation_feedbacck_lines.id),','), ')')
            from cms_qec_evaluation_feedbacck_lines
            WHERE is_valid = true
            group by  name, question
            having count(cms_qec_evaluation_feedbacck_lines.id)  > 1"""
    
        cr.execute(sql)
        qec_rows = cr.fetchall()

        logger.notifyChannel("Records Corrected (cms_qec_evaluation_feedbacck_lines): ", netsvc.LOG_INFO, str(len(qec_rows)))
        for qec_row in qec_rows:
            sql = """select id from cms_qec_evaluation_feedbacck_lines
                where id in """ + str(qec_row[2]) + """
                order by id"""
    
            cr.execute(sql)
            rows = cr.fetchall()
            
            i = 1
            for row in rows:
                if i == 1:
                    i += 1
                    continue
                sql = """UPDATE cms_qec_evaluation_feedbacck_lines set is_valid = False
                    WHERE id = """ + str(row[0])
    
                cr.execute(sql)
                cr.commit()

        return True
    
    def get_teacher_subject_evaluation(self, cr, teacher_id, subject_id):
        qec_qry = """select sum(value), count(value), (sum(value)/(count(value)*5.0))*100 as percentage, qec_evaluation,
            (select name from cms_subject where id = calculated_subject) as subject_name, 
            count(distinct cms_qec_evaluation_feedbacck.id) as students
            from cms_qec_evaluation_feedbacck
            
            inner join cms_qec_evaluation_feedbacck_lines
            on cms_qec_evaluation_feedbacck.id = cms_qec_evaluation_feedbacck_lines.name 
            inner join cms_timetable
            on cms_timetable.id = cms_qec_evaluation_feedbacck.timetable
            inner join cms_qec_evaluation
            on cms_qec_evaluation.id = cms_qec_evaluation_feedbacck.qec_evaluation
            inner join cms_qec_option
            on cms_qec_option.id = cms_qec_evaluation_feedbacck_lines.option
            
            where cms_qec_evaluation_feedbacck_lines.is_valid = true
            AND cms_timetable.teacher = """ + str(teacher_id) + """
            AND cms_timetable.calculated_subject = """ + str(subject_id) + """
            
            AND cms_qec_evaluation_feedbacck_lines.question 
            in (select name from cms_qec_template_lines where statistical_effect is true AND qec_template = cms_qec_evaluation_feedbacck.qec_template)
            
            AND cms_qec_evaluation_feedbacck_lines.question 
            in (SELECT id FROM cms_qec_question WHERE question_area IN (SELECT id FROM cms_qec_question_area WHERE name != 'Course'))
            
            group by qec_evaluation, cms_timetable.calculated_subject, timetable
            order by qec_evaluation desc"""

        cr.execute(qec_qry)
        _rows= cr.fetchall()
        
        #****************** Simple Averages ********************#
        last_sum = 0;
        last_count = 0;
        
        total_sum = 0;
        total_count = 0;
        
        #****************** Weighted Averages ********************#
        last_weighted_sum = 0;
        last_weighted_count = 0;
        
        total_weighted_sum = 0;
        total_weighted_count = 0;
        
        last_flag = True
        
        my_dict = {'last_average': 0.0, 'total_average': 0.0, 'last_weighted_average': 0.0, 'total_weighted_average': 0.0}
        prev_evaluation = None
        current_evalation = None
        
        for _row in _rows:
            current_evalation = _row[3]
            
            if prev_evaluation != None and prev_evaluation != current_evalation and last_flag:
                last_flag = False

            if last_flag:
                #****************** Simple ********************#
                last_sum += _row[2]
                last_count += 1
                
                #****************** Weighted ********************#
                last_weighted_sum += _row[0]
                last_weighted_count += _row[1]
                
            #****************** Simple ********************#
            total_sum += _row[2]
            total_count += 1

            #****************** Weighted ********************#
            total_weighted_sum += _row[0]
            total_weighted_count += _row[1]
            
            prev_evaluation = current_evalation
        
        #****************** Simple ********************#
        
        if last_count > 0:
            my_dict['last_average'] = last_sum/last_count
        if total_count > 0:
            my_dict['total_average'] = total_sum/total_count

        #****************** Weighted ********************#
        if last_weighted_count > 0:
            my_dict['last_weighted_average'] = (last_weighted_sum/(last_weighted_count*5.0))*100
        if total_weighted_count > 0:
            my_dict['total_weighted_average'] = (total_weighted_sum/(total_weighted_count*5.0))*100
        
        return my_dict
    
    def _set_name(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids, context)
        for f in records:
            result[f.id] = str(f.qec_evaluation.name) + " (Tok# " + str(f.feedback_token) + ")"
        return result
    
    def _set_qec_template(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids, context)
        for f in records:
            result[f.id] = f.qec_evaluation.qec_template.id
        return result    
    
    def onchange_evaluation_for(self, cr, uid, ids, context=None):
        vals = {}
        vals['student'] = ''
        vals['employee'] = ''
        vals['timetable'] = ''
         
        return {'value':vals}
    
    def onchange_evaluation(self, cr, uid, ids, feedback_token, student, employee, timetable, qec_evaluation, context=None):
        vals = {}
        
        if not type(ids) is list:
            ids = [ids]
            
        template = self.pool.get('cms.qec.evaluation').browse(cr, uid, qec_evaluation, context).qec_template.id
        if not template:
            return {'value':vals}
        
        template_obj = self.pool.get('cms.qec.template').browse(cr, uid, template, context)
        template_lines_ids = self.pool.get('cms.qec.template.lines').search(cr, uid, [('qec_template', '=', template)], context)
        template_lines_objs = self.pool.get('cms.qec.template.lines').browse(cr, uid, template_lines_ids, context)
        
        evaluation_feedbacck_lines = []
        
        if ids:
            evaluation_feedbacck_lines_delete_ids = []
            for template_lines_obj in template_lines_objs:
                evaluation_feedbacck_lines_ids = self.pool.get('cms.qec.evaluation.feedbacck.lines').search(cr, uid, [('name', 'in', ids),('serial_no', '=', template_lines_obj.serial_no),('question', '=', template_lines_obj.name.id)], context)
                evaluation_feedbacck_lines_delete_ids.extend(evaluation_feedbacck_lines_ids)
                
                if not evaluation_feedbacck_lines_ids:
                    evaluation_feedbacck_lines.append((0,0, {'serial_no':template_lines_obj.serial_no, 'question':template_lines_obj.name.id, 'option':None}))
            
            evaluation_feedbacck_lines_ids = self.pool.get('cms.qec.evaluation.feedbacck.lines').search(cr, uid, [('name', 'in', ids),('id', 'not in', evaluation_feedbacck_lines_delete_ids)], context)
            self.pool.get('cms.qec.evaluation.feedbacck.lines').unlink(cr, uid, evaluation_feedbacck_lines_ids, context)
            
        else:
            for template_lines_obj in template_lines_objs:
                evaluation_feedbacck_lines.append((0,0, {'serial_no':template_lines_obj.serial_no, 'question':template_lines_obj.name.id, 'option':None}))
        
        if not ids:
            evaluation_feedbacck_new_lines = []
            
            evaluation_feedbacck_exist_id = self.pool.get('cms.qec.evaluation.feedbacck').search(cr, uid, [('feedback_token', '=', feedback_token)])
            if evaluation_feedbacck_exist_id:
                evaluation_feedbacck_obj = self.pool.get('cms.qec.evaluation.feedbacck').browse(cr, uid, evaluation_feedbacck_exist_id[0], context)
                if evaluation_feedbacck_obj.student:
                    student = evaluation_feedbacck_obj.student.id
                    vals['student'] = evaluation_feedbacck_obj.student.id
                if evaluation_feedbacck_obj.employee:
                    employee = evaluation_feedbacck_obj.employee.id
                    vals['employee'] = evaluation_feedbacck_obj.employee.id
                if evaluation_feedbacck_obj.timetable:
                    timetable = evaluation_feedbacck_obj.timetable.id
                    vals['timetable'] = evaluation_feedbacck_obj.timetable.id
                    
                for evaluation_feedbacck_line in evaluation_feedbacck_lines:
                    if 'question' in evaluation_feedbacck_line[2]:
                        evaluation_feedbacck_line_exist = self.pool.get('cms.qec.evaluation.feedbacck.lines').\
                            search(cr, uid, [('name', '=', evaluation_feedbacck_exist_id[0]),('question', '=', evaluation_feedbacck_line[2]['question'])])
                    
                        if not evaluation_feedbacck_line_exist:
                            evaluation_feedbacck_new_lines.append(evaluation_feedbacck_line)
            else:
                evaluation_feedbacck_new_lines = evaluation_feedbacck_lines
                
            evaluation_feedbacck_id = self.pool.get('cms.qec.evaluation.feedbacck').\
                create(cr,uid,{'feedback_token':feedback_token,'evaluation_for':template_obj.evaluation_for,'student':student,'employee':employee,
                'timetable':timetable,'qec_template':template,'evaluation_feedbacck_lines':evaluation_feedbacck_new_lines,'state':'Draft'}, context)    
            
            evaluation_feedbacck_id = [evaluation_feedbacck_id]
            vals['active_id'] = evaluation_feedbacck_id
        else:
            evaluation_feedbacck_id = ids
            self.pool.get('cms.qec.evaluation.feedbacck').write(cr,uid, ids, {'feedback_token':feedback_token,'evaluation_for':template_obj.evaluation_for,'student':student,'employee':employee,'timetable':timetable,'evaluation_feedbacck_lines':evaluation_feedbacck_lines}, context)
        
        evaluation_feedbacck_lines_ids = self.pool.get('cms.qec.evaluation.feedbacck.lines').search(cr, uid, [('name', 'in', evaluation_feedbacck_id)])
        vals['evaluation_for'] = template_obj.evaluation_for
        vals['evaluation_feedbacck_lines'] = evaluation_feedbacck_lines_ids
        
        return {'value':vals}

    _name= "cms.qec.evaluation.feedbacck"
    _descpription = "QEC Evaluation"

    name= fields.function(_set_name, method=True, string='Name', type='char', size=300, store=True)
    qec_evaluation= fields.many2one('cms.qec.evaluation', 'Evaluation', required=True)
    feedback_token= fields.char('Feedback Token', size=50)
    evaluation_for= fields.related('qec_template', 'evaluation_for', string='Evaluation For',size=30, type='char', store=True, readonly=True)
    student= fields.many2one('cms.entryregis', 'For (Student)')
    employee= fields.many2one('hr.employee', 'For (Employee)')
    timetable= fields.many2one('cms.timetable', 'Subject (Timetable)')
    qec_template= fields.related('qec_evaluation', 'qec_template', string='QEC Template', type='many2one', relation='cms.qec.template', store=True, readonly=True)
    evaluation_feedbacck_lines= fields.one2many('cms.qec.evaluation.feedbacck.lines','name', 'Evaluation Feedbacks', required=True)
    state= fields.selection([('Draft','Draft'),('Completed','Completed'),('Reopen','Re-Opened')],'State', required=True)
    readonly_state= fields.related('qec_evaluation', 'state', string='Read-only State',size=30, type='char', readonly=True)
    is_valid=fields.boolean('Is Valid', required=True)
    
    completed_by= fields.many2one('res.users', 'Completed By')
    completed_date= fields.date('Completed Date')
    
    reopen_by= fields.many2one('res.users', 'Reopen By')
    reopen_date= fields.date('Reopen Date')
    
    recomplete_by= fields.many2one('res.users', 'Re-Completed By')
    recomplete_date= fields.date('Re-completed Date')
    
    _sql_constraints = [
        ('unique_evaluation', 'unique (qec_evaluation,feedback_token,student,employee,timetable)', 'QEC Evaluation must be unique!')]
    
    _defaults = {
        'evaluation_for': lambda *a: '',
        'state': lambda *a: 'Draft',
        'is_valid': lambda *a: True,
    }
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = None
        rec_id = None
          
        if 'feedback_token' in vals and 'qec_evaluation' in vals and 'student' in vals and 'employee' in vals and 'timetable' in vals:
            if vals['feedback_token']:
                
                feedback_token = None
                timetable = None
                qec_evaluation = None
                student = None
                employee = None
                
                if vals['feedback_token']:
                    feedback_token = str(vals['feedback_token'])
                if vals['timetable']:
                    timetable = int(vals['timetable'])
                if vals['qec_evaluation']:
                    qec_evaluation = int(vals['qec_evaluation'])
                if vals['student']:
                    student = int(vals['student'])
                if vals['employee']:
                    employee = int(vals['employee'])
                
                rec_id = self.pool.get('cms.qec.evaluation.feedbacck').search(cr, uid, [('feedback_token', '=', feedback_token),
                                        ('timetable', '=', timetable),('qec_evaluation', '=', qec_evaluation),
                                        ('student', '=', student),('employee', '=', employee)])
            if rec_id:
                result = rec_id[0]
                #self.write(cr, uid, rec_id, vals)
            else:
                result = super(models.Model, self).create(cr, uid, vals, context)
                
        return result

class cms_qec_evaluation_feedbacck_lines(models.Model):

    _name= "cms.qec.evaluation.feedbacck.lines"
    _descpription = "QEC Evaluation Lines"

    name= fields.many2one('cms.qec.evaluation.feedbacck','Evaluation', required=True)       
    question= fields.many2one('cms.qec.question','Question', required=True)     
    option= fields.many2one('cms.qec.option','Option', domain="[('qec_question','=',question)]")     
    text= fields.text('Comments')      
    serial_no= fields.integer('Serial No', required=True)
    sequence_no= fields.char('Sequence No', size=30 )
    readonly_state= fields.related('name','qec_evaluation', 'state', string='Read-only State',size=30, type='char', readonly=True)
    is_valid=fields.boolean('Is Valid', required=True)

    
    _defaults = {
        'is_valid': lambda *a: True,
    }
    
    _sql_constraints = [
        ('unique_feedback_question_', 'unique (name,question,is_valid)', 'Student Question Feedback must be unique for an evaluation!'),]
    
    


