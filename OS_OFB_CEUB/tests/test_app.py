from app import app, db

def test_login_page():
 app.config.update(TESTING=True,WTF_CSRF_ENABLED=False)
 with app.test_client() as c:
  r=c.get('/login'); assert r.status_code==200; assert 'Acesso ao OS/OFB'.encode() in r.data

def test_protected_redirect():
 app.config.update(TESTING=True)
 with app.test_client() as c:
  r=c.get('/',follow_redirects=False); assert r.status_code==302; assert '/login' in r.headers['Location']

def test_login_and_dashboard():
 app.config.update(TESTING=True,WTF_CSRF_ENABLED=False)
 with app.test_client() as c:
  r=c.post('/login',data={'username':'admin','password':'Admin@123'},follow_redirects=True)
  assert r.status_code==200; assert 'Painel de execução'.encode() in r.data
