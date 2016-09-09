#coding:utf-8
from flask import Flask,request,render_template,jsonify,redirect,url_for,flash
from flask_migrate import Migrate,MigrateCommand
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from datetime import datetime
import os,sys
import traceback

app = Flask(__name__)
app.debug = True
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)),'data.sqlite')
app.config["SECRET_KEY"] = "really hard to guess"
db = SQLAlchemy()
manager = Manager(app)
migrate = Migrate(app,db)
manager.add_command('db',MigrateCommand)
db.init_app(app)


class Keeper(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(32))
    desc = db.Column(db.String(128))
    status = db.Column(db.Integer,default=0)
    createdtime = db.Column(db.DateTime,default=datetime.now)

    def __init__(self,name,desc):
        self.name = name
        self.desc = desc

    def __repr__(self):
        return "<Keeper:%s:%s>" %(self.name,self.desc)

class Door(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    desc = db.Column(db.String(32))
    link = db.Column(db.String(256))
    keeperid = db.Column(db.Integer)
    status = db.Column(db.Integer,default=0)
    createdtime = db.Column(db.DateTime,default=datetime.now)

    def __init__(self,desc,link,keeperid):
        self.desc = desc
        self.link = link
        self.keeperid = keeperid

    def __repr__(self):
        return "<Door:%s>" % self.desc

@manager.command
def dbinit():
	db.create_all()
	print('dbinit ok')

@manager.command
def dbdrop():
	db.drop_all()
	print('ok')

@app.route("/")
def keepers():
	return render_template("keeper.html")

@app.route("/keeper/add",methods=["post"])
def addKeeper():
	message = None
	name = request.form.get("name")
	desc = request.form.get("desc")
	try:
		ca = Keeper.query.filter_by(name=name).first()
		if not ca:
			keeper = Keeper(name=name,desc=desc)
			db.session.add(keeper)
			db.session.commit()
			message = {"type":"success","message":"新增成功！"}
		else:
			message = {"type":"error","message":"[error]:'%s'名称已被占用！" %name}
	except Exception as e:
		message = {"type":"error","message":"[error]:%s|%s" %(str(e),traceback.format_exc())}

	flash(message)
	return redirect(url_for("keepers"))


@app.route("/keeper/all")
def allKeeper():
	keepers = Keeper.query.filter_by(status=0).all()
	data = [{"id":i+1,"name":"<a href='/%s/'>%s</a>" %(c.id,c.name),"desc":c.desc,"operation":"<a href='#' onclick=del(%s)>删除</a>" %c.id} for i,c in enumerate(keepers)]
	return jsonify(data)


@app.route("/keeper/delete/<id>",methods=["delete"])
def delKeeper(id):
	info = {"result":True,"errorMsg":None}
	try:
		keeper = Keeper.query.filter_by(id=id).first()
		if keeper:
			keeper.status = -1
			db.session.add(keeper)
			db.session.commit()
			message = {"type":"success","message":"'%s'删除成功!" %keeper.name}
			flash(message)
	except Exception as e:
		info["result"] = False 
		info["errorMsg"] = "[error]:%s|%s" %(str(e),traceback.format_exc())
	finally:
		return jsonify(info)


@app.route("/<keeperid>/")
def viewKeeper(keeperid):
	keeper = Keeper.query.filter_by(id=keeperid).first()
	if keeper:
		return render_template("door.html",keeperid=keeperid,keepername=keeper.name)
	else:
		return render_template("404.html")


@app.route("/<keeperid>/add",methods=["post"])
def addDoor(keeperid):
	message = None
	desc = request.form.get("desc")
	link = request.form.get("link")
	try:
		keeper = Keeper.query.filter_by(id=keeperid).first()
		if keeper:
			d = Door.query.filter_by(desc=desc).all()
			door = Door(desc="%s_%s" %(desc,len(d)) if d else desc,link=link,keeperid=keeperid)
			db.session.add(door)
			db.session.commit()
			message = {"type":"success","message":"新增成功！"}
		else:
			message = {"type":"error","message":"新增失败,该分类不存在或已被删除！"}
	except Exception as e:
		message = {"type":"error","message":"新增失败,errorMsg:%s|%s" %(str(e),traceback.format_exc())}

	flash(message)
	return redirect(url_for("viewKeeper",keeperid=keeperid))


@app.route("/<keeperid>/all")
def allDoor(keeperid):
	doors = Door.query.filter_by(keeperid=keeperid).filter_by(status=0).all()
	data = [{"id":i+1,"desc":"%s" %d.desc,"link":"<a href='%s' target='_blank'>%s</a>" %(d.link,d.link),"operation":"<a href='#' onclick=del(%s)>删除</a>" %d.id} for i,d in enumerate(doors)]
	return jsonify(data)


@app.route("/door/delete/<id>",methods=["delete"])
def delDoor(id):
	info = {"result":True,"errorMsg":None}
	try:
		door = Door.query.filter_by(id=id).first()
		if door:
			door.status = -1
			db.session.add(door)
			db.session.commit()
			message = {"type":"success","message":"'%s'删除成功!" %door.desc}
			flash(message)
	except Exception as e:
		info["result"] = False 
		info["errorMsg"] = "[error]%s|%s" %(str(e),traceback.format_exc())
	finally:
		return jsonify(info)


if __name__ == "__main__":
	manager.run()
