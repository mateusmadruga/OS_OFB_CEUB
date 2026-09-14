import csv, io, time
from functools import wraps
from datetime import date
from decimal import Decimal
from flask import Flask, render_template, redirect, url_for, flash, request, abort, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import or_, func
from config import Config
from models import db, User, Contract, ServiceOrder, WorkflowEvent, AuditLog
from forms import LoginForm, ContractForm, OrderForm, TransitionForm

app=Flask(__name__); app.config.from_object(Config); db.init_app(app); csrf=CSRFProtect(app)
login=LoginManager(app); login.login_view='login_view'; login.login_message='Entre para acessar o sistema.'
FAILED={}
ROLES={'admin','gestor_contrato','fiscal_tecnico','fiscal_requisitante','fiscal_administrativo','contratada'}
TRANSITIONS={
 'emitida':[('entregar','Objeto entregue','recebimento_provisorio',{'contratada','admin'})],
 'recebimento_provisorio':[('receber_provisorio','Recebimento provisório','avaliacao_qualidade',{'fiscal_tecnico','admin'})],
 'avaliacao_qualidade':[('conforme','Avaliação conforme','avaliacao_aderencia',{'fiscal_tecnico','fiscal_requisitante','admin'}),('nao_conforme','Não conformidade','demanda_correcao',{'fiscal_tecnico','fiscal_requisitante','admin'})],
 'avaliacao_aderencia':[('aderente','Aderente','recebimento_definitivo',{'fiscal_administrativo','admin'}),('nao_aderente','Não aderente','demanda_correcao',{'fiscal_administrativo','admin'})],
 'demanda_correcao':[('corrigido','Correção entregue','recebimento_provisorio',{'contratada','admin'})],
 'recebimento_definitivo':[('receber_definitivo','Recebimento definitivo','glosa_sancao',{'fiscal_tecnico','fiscal_requisitante','admin'})],
 'glosa_sancao':[('verificar','Glosa/sanção verificada','faturamento',{'gestor_contrato','fiscal_administrativo','admin'})],
 'faturamento':[('autorizar','Faturamento autorizado','nota_fiscal',{'gestor_contrato','admin'})],
 'nota_fiscal':[('emitir_nf','Nota fiscal registrada','regularidades',{'contratada','admin'})],
 'regularidades':[('regular','Regularidades comprovadas','liquidacao',{'fiscal_administrativo','admin'}),('irregular','Pendência documental','regularidades',{'fiscal_administrativo','admin'})],
 'liquidacao':[('pagar','Pagamento registrado','paga',{'fiscal_administrativo','admin'})]
}
@login.user_loader
def load_user(i): return db.session.get(User,int(i))
def roles(*allowed):
 def deco(fn):
  @wraps(fn)
  def wrap(*a,**k):
   if current_user.role not in allowed: abort(403)
   return fn(*a,**k)
  return wrap
 return deco
def audit(action,entity,eid=None,detail=''):
 db.session.add(AuditLog(actor_id=current_user.id if current_user.is_authenticated else None,action=action,entity=entity,entity_id=eid,detail=detail,ip=request.headers.get('X-Forwarded-For',request.remote_addr)))
@app.after_request
def headers(r):
 r.headers['X-Content-Type-Options']='nosniff'; r.headers['X-Frame-Options']='DENY'; r.headers['Referrer-Policy']='strict-origin-when-cross-origin'
 r.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; script-src 'self' https://cdn.jsdelivr.net; font-src https://cdn.jsdelivr.net; img-src 'self' data:"
 return r
@app.route('/login',methods=['GET','POST'])
def login_view():
 form=LoginForm(); key=request.remote_addr or 'local'; nowt=time.time(); attempts=[t for t in FAILED.get(key,[]) if nowt-t<300]; FAILED[key]=attempts
 if len(attempts)>=5: abort(429)
 if form.validate_on_submit():
  u=User.query.filter_by(username=form.username.data.strip()).first()
  if u and u.check_password(form.password.data) and u.active:
   FAILED[key]=[]; login_user(u); audit('LOGIN','User',u.id); db.session.commit(); return redirect(url_for('dashboard'))
  FAILED[key].append(nowt); flash('Credenciais inválidas.','danger')
 return render_template('login.html',form=form)
@app.route('/logout',methods=['POST'])
@login_required
def logout(): audit('LOGOUT','User',current_user.id); db.session.commit(); logout_user(); return redirect(url_for('login_view'))
@app.route('/')
@login_required
def dashboard():
 stats={s:c for s,c in db.session.query(ServiceOrder.status,func.count(ServiceOrder.id)).group_by(ServiceOrder.status).all()}
 total=db.session.query(func.coalesce(func.sum(ServiceOrder.value),0)).scalar()
 latest=ServiceOrder.query.order_by(ServiceOrder.updated_at.desc()).limit(8).all()
 return render_template('dashboard.html',stats=stats,total=total,latest=latest)
@app.route('/contracts')
@login_required
def contracts(): return render_template('contracts.html',items=Contract.query.order_by(Contract.number).all())
@app.route('/contracts/new',methods=['GET','POST'])
@login_required
@roles('admin','gestor_contrato')
def contract_new():
 f=ContractForm()
 if f.validate_on_submit():
  if f.end_date.data<f.start_date.data: flash('Data final deve ser posterior à inicial.','danger')
  else:
   x=Contract(number=f.number.data.strip(),supplier=f.supplier.data.strip(),object=f.object.data.strip(),total_value=f.total_value.data,start_date=f.start_date.data,end_date=f.end_date.data)
   db.session.add(x); db.session.flush(); audit('CREATE','Contract',x.id,x.number); db.session.commit(); flash('Contrato cadastrado.','success'); return redirect(url_for('contracts'))
 return render_template('form.html',form=f,title='Novo contrato')
@app.route('/contracts/<int:id>/edit',methods=['GET','POST'])
@login_required
@roles('admin','gestor_contrato')
def contract_edit(id):
 x=db.get_or_404(Contract,id); f=ContractForm(obj=x)
 if f.validate_on_submit():
  f.populate_obj(x); audit('UPDATE','Contract',x.id,x.number); db.session.commit(); flash('Contrato atualizado.','success'); return redirect(url_for('contracts'))
 return render_template('form.html',form=f,title='Editar contrato')
@app.route('/orders')
@login_required
def orders():
 q=ServiceOrder.query; term=request.args.get('q','').strip(); status=request.args.get('status','').strip()
 if term: q=q.filter(or_(ServiceOrder.number.ilike(f'%{term}%'),ServiceOrder.description.ilike(f'%{term}%')))
 if status: q=q.filter_by(status=status)
 return render_template('orders.html',items=q.order_by(ServiceOrder.updated_at.desc()).all(),term=term,status=status,statuses=sorted(TRANSITIONS.keys()|{'paga'}))
@app.route('/orders/new',methods=['GET','POST'])
@login_required
@roles('admin','gestor_contrato')
def order_new():
 f=OrderForm(); f.contract_id.choices=[(c.id,f'{c.number} · {c.supplier}') for c in Contract.query.order_by(Contract.number).all()]
 if not f.contract_id.choices: flash('Cadastre um contrato antes da OS/OFB.','warning'); return redirect(url_for('contract_new'))
 if f.validate_on_submit():
  x=ServiceOrder(number=f.number.data.strip(),contract_id=f.contract_id.data,kind=f.kind.data,description=f.description.data.strip(),value=f.value.data,due_date=f.due_date.data,created_by=current_user.id)
  db.session.add(x); db.session.flush(); db.session.add(WorkflowEvent(order_id=x.id,action='emitir',to_status='emitida',notes='OS/OFB emitida',actor_id=current_user.id)); audit('CREATE','ServiceOrder',x.id,x.number); db.session.commit(); flash('OS/OFB emitida.','success'); return redirect(url_for('order_detail',id=x.id))
 return render_template('form.html',form=f,title='Emitir OS/OFB')
@app.route('/orders/<int:id>')
@login_required
def order_detail(id):
 x=db.get_or_404(ServiceOrder,id); f=TransitionForm(); choices=[]
 for code,label,target,allowed in TRANSITIONS.get(x.status,[]):
  if current_user.role in allowed: choices.append((code,label))
 f.action.choices=choices
 return render_template('order_detail.html',o=x,form=f,choices=choices)
@app.route('/orders/<int:id>/transition',methods=['POST'])
@login_required
def transition(id):
 x=db.get_or_404(ServiceOrder,id); f=TransitionForm(); options=TRANSITIONS.get(x.status,[]); f.action.choices=[(a,b) for a,b,_,allowed in options if current_user.role in allowed]
 if not f.validate_on_submit(): flash('Etapa inválida ou evidência insuficiente.','danger'); return redirect(url_for('order_detail',id=id))
 match=next((z for z in options if z[0]==f.action.data and current_user.role in z[3]),None)
 if not match: abort(403)
 old=x.status; x.status=match[2]; db.session.add(WorkflowEvent(order_id=x.id,action=match[0],from_status=old,to_status=x.status,notes=f.notes.data.strip(),actor_id=current_user.id)); audit('TRANSITION','ServiceOrder',x.id,f'{old} -> {x.status}'); db.session.commit(); flash('Etapa registrada com trilha de auditoria.','success'); return redirect(url_for('order_detail',id=id))
@app.route('/reports')
@login_required
def reports():
 rows=db.session.query(ServiceOrder.status,func.count(ServiceOrder.id),func.coalesce(func.sum(ServiceOrder.value),0)).group_by(ServiceOrder.status).all()
 return render_template('reports.html',rows=rows)
@app.route('/reports/orders.csv')
@login_required
def report_csv():
 out=io.StringIO(); w=csv.writer(out); w.writerow(['Número','Tipo','Contrato','Descrição','Valor','Status','Prazo'])
 for o in ServiceOrder.query.order_by(ServiceOrder.number): w.writerow([o.number,o.kind,o.contract.number,o.description,str(o.value),o.status,o.due_date.isoformat() if o.due_date else ''])
 audit('EXPORT','ServiceOrder',detail='CSV'); db.session.commit(); return Response('\ufeff'+out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=relatorio_os_ofb.csv'})
@app.route('/audit')
@login_required
@roles('admin','gestor_contrato')
def audit_view(): return render_template('audit.html',items=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all())
@app.errorhandler(403)
def e403(e): return render_template('error.html',code=403,msg='Acesso não autorizado para este perfil.'),403
@app.errorhandler(404)
def e404(e): return render_template('error.html',code=404,msg='Registro não encontrado.'),404
@app.errorhandler(429)
def e429(e): return render_template('error.html',code=429,msg='Muitas tentativas. Tente novamente após alguns minutos.'),429

def seed():
 db.create_all()
 if not User.query.first():
  for name,user,email,role,pwd in [('Administrador','admin','admin@aula.local','admin','Admin@123'),('Gestor do Contrato','gestor','gestor@aula.local','gestor_contrato','Gestor@123'),('Fiscal Técnico','fiscaltec','fiscaltec@aula.local','fiscal_tecnico','Fiscal@123'),('Fiscal Requisitante','fiscalreq','fiscalreq@aula.local','fiscal_requisitante','Fiscal@123'),('Fiscal Administrativo','fiscaladm','fiscaladm@aula.local','fiscal_administrativo','Fiscal@123'),('Contratada','contratada','contratada@aula.local','contratada','Empresa@123')]:
   u=User(name=name,username=user,email=email,role=role); u.set_password(pwd); db.session.add(u)
  db.session.commit()
 if not Contract.query.first():
  c=Contract(number='CT-001/2026',supplier='Fornecedor Demonstração Ltda.',object='Prestação de serviços de TIC para demonstração acadêmica.',total_value=Decimal('250000.00'),start_date=date(2026,1,1),end_date=date(2026,12,31)); db.session.add(c); db.session.commit()
with app.app_context(): seed()
if __name__=='__main__': app.run(host='127.0.0.1',port=5000,debug=False)
