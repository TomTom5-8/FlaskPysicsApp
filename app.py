from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import numpy as np
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
JST = timezone(timedelta(hours=+9))

app = Flask(__name__)

# セッション用の秘密鍵
app.config['SECRET_KEY'] = 'tom05' 

#DBの設定
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,'physics.db')
db = SQLAlchemy(app)

# ログイン管理の設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # 未ログイン時に飛ばす先

## --- モデルの定義 ---
# ユーザーモデル
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    # ユーザーと履歴の紐付け（1対多）
    histories = db.relationship('SimulationHistory', backref='author', lazy=True)

# 履歴モデル（user_idを追加）
class SimulationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    k = db.Column(db.Float, nullable=False)
    gamma = db.Column(db.Float, nullable=False)
    x0 = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(JST))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 初回実行時にDBファイルを作成する
with app.app_context():
    db.create_all()

# --- ルーティング ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # ユーザー名の重複チェック
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('そのユーザー名は既に使われています。')
            return redirect(url_for('register'))
        
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        flash('登録が完了しました！ログインしてください。')
        return redirect(url_for('login'))
    
    return render_template('register.html') # HTMLファイルを読み込む

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが正しくありません。')
            
    return render_template('login.html') # HTMLファイルを読み込む

@app.route('/logout')
def logout():
    logout_user()
    flash('ログアウトしました。') # メッセージを追加
    return redirect(url_for('login'))

@app.route('/')
@login_required #login必須に
def index():
    return render_template('index.html', user=current_user)
@app.route('/calculate')
@login_required
def calculate():
    #パラメーター（後ほどUser入力に変更)
    k = float(request.args.get('k', 1.0))#ばね定数 1.0はデフォルト
    m = float(request.args.get('m', 1.0)) #質量
    gamma = float(request.args.get('gamma', 0.1)) #減衰定数
    x0 = float(request.args.get('x0', 10)) #初期変位
    #v0 = 0.1 #初速
    t_max = float(request.args.get('t_max', 50)) # 時間(秒)
    dt = 0.1 #刻み幅

    # DBに保存 ログイン中のユーザーIDで保存
    new_history = SimulationHistory(k=k, gamma=gamma, x0=x0, user_id=current_user.id)
    db.session.add(new_history)
    db.session.commit()

    t= np.arange(0,t_max,dt)

    # 運動方程式 m*x'' + gamma*x' + k*x = 0 を解く
    # 簡単のため、減衰振動の一般解（不足減衰の場合）を使います
    omega0 = np.sqrt(k/m)
    zeta =  gamma / (2*np.sqrt(m*k))
    if zeta >=1.0 :zeta=0.99

    omega_d = omega0 * np.sqrt(1-zeta**2)

    # 変位 x(t) の計算
    x = np.exp(-zeta * omega0 * t) * (x0 * np.cos(omega_d * t))

    # JSONで返せるようにリスト形式に変換
    return jsonify({
        "t": t.tolist(),
        "x": x.tolist()
    })

@app.route('/history')
def get_history():
    #DBから履歴を取得(自分のみ)
    histories = SimulationHistory.query.filter_by(user_id=current_user.id).order_by(SimulationHistory.timestamp.desc()).all()
    history_list = []
    for h in histories:
        history_list.append({
            'id': h.id, 'k':h.k, 'gamma':h.gamma, 'x0':h.x0, 'timestamp':h.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(history_list)




if __name__ == '__main__':
    app.run(debug=True)
  