from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from datetime import datetime

from .db import get_db
from .auth import login_required
from .constants import measure_units,status_list
from .part_utils import(
    get_all_parts, get_orphan_parts, get_part_info, generate_bom, get_last_number, get_project_prefixes, increment_number,update_quantity, get_part_list
)

bp = Blueprint('part', __name__, url_prefix='/part')


@bp.route('/menu',methods=('GET',))
def menu():
    return render_template('part/common.html')

@bp.route('/all',methods=('GET',))
def all():
    parts = get_all_parts()
    return render_template('part/list.html',parts=parts)

@bp.route('/orphan',methods=('GET',))
def orphan():
    parts = get_orphan_parts()
    return render_template('part/list.html',parts=parts)


@bp.route('/search', methods=('GET', 'POST'))
def search():
    if request.method=='GET':
        parts = []
    elif request.method=='POST':
        db=get_db()
        search_term:str = str(request.form['search_term'])
        print(search_term)
        parts = db.execute(
            'SELECT *'
            ' FROM part'
            ' WHERE name LIKE ? OR part_number LIKE ?'
            ,(f'%{search_term}%', f'%{search_term}%')
        ).fetchall()

    return render_template('part/search.html',parts=parts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    
    prefixes:list[str] = get_project_prefixes()

    if request.method=='GET':
        return render_template('/part/create.html', units=measure_units, prefixes=prefixes)
    

    if request.method=='POST':
 
        prefix:str = request.form['prefix']
        name:str = request.form['name']
        measure_unit:str = request.form['measure_unit']
        last_pn:int = get_last_number(prefix=prefix)
        part_number = f"{prefix}-{str(last_pn+1).zfill(4)}"
 
        db=get_db()
        db.execute(
            'INSERT into part (part_number, name, measure_unit, owner, status)'
            ' VALUES (?,?,?,?,?)',
            (part_number, name, measure_unit, g.user['username'],"creation")
        )
        db.commit()
        increment_number(prefix=prefix,last_number=last_pn)


        return redirect(f'/part/{part_number}')
    

@bp.route('/<string:part_number>', methods=('GET',))
def view(part_number):

    part = get_part_info(part_number=part_number)
    bom = generate_bom(part_number=part_number)

    return render_template('part/info.html', part=part, bom=bom)


@bp.route('/<string:part_number>/edit_structure', methods=('GET','POST'))
@login_required
def edit_structure(part_number):
    if request.method=='GET':
        part = get_part_info(part_number=part_number)
        bom = generate_bom(part_number=part_number)
    
    return render_template('part/edit_structure.html', part=part, bom=bom)


@bp.route('/<string:part_number>/edit_info', methods=('GET','POST'))
@login_required
def edit_info(part_number):
    if request.method=='GET':
        part = get_part_info(part_number=part_number)
        bom = generate_bom(part_number=part_number)
        return render_template('part/edit_info.html', part=part, bom=bom, units=measure_units, status_list=status_list)
        
    if request.method=='POST':
        print(dict(request.form))
        name=request.form['name']
        measure_unit=request.form['measure_unit']
        status=request.form['status']
        last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        db=get_db()
        db.execute(
            'UPDATE part'
            ' SET name = ?, measure_unit = ?, status=?, last_modified=?'
            ' WHERE part_number = ?',
            (name,measure_unit,status,last_modified,part_number)
        )
        db.commit()

    part = get_part_info(part_number=part_number)
    bom = generate_bom(part_number=part_number)
    return redirect(f'/part/{part_number}')


@bp.route('/quantity/<string:pn>/<string:parent_pn>', methods=('POST',))
@login_required
def set_quantity_child_in_parent(pn,parent_pn):

    quantity=request.form['quantity']
    view_pn = request.form['view_pn']
    update_quantity(child_part=pn,parent_part=parent_pn,quantity=quantity)
    
    return redirect(f"/part/{view_pn}/edit_structure")


@bp.route('/delete/<string:pn>/<string:parent_pn>', methods=('GET','POST'))
@login_required

def set_delete_child_from_parent(pn,parent_pn):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    db=get_db()
    db.execute('DELETE FROM bom WHERE part_number=? AND parent_part_number=?',(pn,parent_pn))
    db.execute('UPDATE part SET last_modified=? WHERE part_number=?',(now,parent_pn))
    db.commit()

    return redirect(f"/part/AAAA-0001/edit_structure")


@bp.route('<string:parent_pn>/add_child', methods=('POST',))
def add_child(parent_pn):
    db=get_db()
    child_pn = request.form['new_child']
    
    existing_parts = get_part_list()
    if child_pn not in existing_parts:
        flash(f'ERROR - {child_pn} does not exist in database. Create part before adding it')
        return redirect(f"/part/{parent_pn}/edit_structure")

    if parent_pn == child_pn:
        flash(f'ERROR - stop trying to break the database.\n Kindly, the admin')
        return redirect(f"/part/{parent_pn}/edit_structure")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        db.execute(
            'INSERT INTO bom (part_number,parent_part_number,quantity)'
            'VALUES (?,?,1)',
            (child_pn,parent_pn)
        )
        db.execute('UPDATE part SET last_modified=? WHERE part_number=?',(now,parent_pn))
        db.commit()
    except db.IntegrityError:
        flash(f"{child_pn} number is already in {parent_pn}. Change quantity isntead")
    
    return redirect(f"/part/{parent_pn}/edit_structure")


