from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
class LoginForm(FlaskForm):
    username=StringField('Usuário',validators=[DataRequired(),Length(max=80)])
    password=PasswordField('Senha',validators=[DataRequired(),Length(max=128)])
    submit=SubmitField('Entrar')
class ContractForm(FlaskForm):
    number=StringField('Número',validators=[DataRequired(),Length(max=50)]); supplier=StringField('Contratada',validators=[DataRequired(),Length(max=160)])
    object=TextAreaField('Objeto',validators=[DataRequired(),Length(max=4000)]); total_value=DecimalField('Valor total',validators=[DataRequired(),NumberRange(min=0)],places=2)
    start_date=DateField('Início',validators=[DataRequired()]); end_date=DateField('Fim',validators=[DataRequired()]); submit=SubmitField('Salvar contrato')
class OrderForm(FlaskForm):
    number=StringField('Número',validators=[DataRequired(),Length(max=50)]); contract_id=SelectField('Contrato',coerce=int,validators=[DataRequired()])
    kind=SelectField('Tipo',choices=[('OS','Ordem de Serviço'),('OFB','Ordem de Fornecimento de Bens')]); description=TextAreaField('Descrição',validators=[DataRequired(),Length(max=4000)])
    value=DecimalField('Valor',validators=[DataRequired(),NumberRange(min=0)],places=2); due_date=DateField('Prazo',validators=[DataRequired()]); submit=SubmitField('Emitir OS/OFB')
class TransitionForm(FlaskForm):
    action=SelectField('Ação',validators=[DataRequired()]); notes=TextAreaField('Evidência / observações',validators=[DataRequired(),Length(min=5,max=4000)]); submit=SubmitField('Registrar etapa')
