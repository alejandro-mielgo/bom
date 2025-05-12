from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from datetime import datetime

from .db import get_db
from .auth import login_required
from .constants import measure_units,status_list

bp = Blueprint('part', __name__, url_prefix='/part')


def get_project_prefixes()->list[str]:
    db=get_db()
    prefixes = db.execute(
        'SELECT prefix FROM project'
    ).fetchall()
    return [prefix['prefix'] for prefix in prefixes]


def get_last_number(prefix:str)->int:
    db=get_db()
    number = db.execute(
        'SELECT last_pn FROM project WHERE prefix=?',(prefix,)
    ).fetchone()
    return(int(number['last_pn']))


def increment_number(prefix:str,last_number:int)->None:
    db=get_db()
    db.execute(
        'UPDATE project'
        ' SET last_pn=?'
        ' WHERE prefix=?',
        (last_number+1,prefix)
    )
    db.commit()


def get_part_info(part_number:str)->dict:
    db=get_db()
    part = db.execute(
        'SELECT * FROM part JOIN user ON part.owner_id=user.id'
        ' WHERE part_number=?',(part_number,)
    ).fetchone()
    print(dict(part))
    return part


def get_all_parts():
    db=get_db()
    parts = db.execute('SELECT * FROM part').fetchall()
    return parts


def get_orphan_parts():
    db=get_db()
    parts = db.execute(
        """
        SELECT *
        FROM part LEFT JOIN bom ON part.part_number = bom.part_number
        WHERE bom.part_number IS NULL
        """
    ).fetchall()
    return parts

def generate_bom(part_number: str)->dict:
    db = get_db()
    child_parts = db.execute(
    '''
    WITH RECURSIVE under_parent_part_number(part_number, parent_part_number, quantity, level, path) AS (
        SELECT ?, NULL, NULL, 0, ?
        UNION ALL
        SELECT 
            bom.part_number, 
            bom.parent_part_number,
            bom.quantity,
            upp.level + 1,
            upp.path || ' > ' || bom.part_number
        FROM bom 
        JOIN under_parent_part_number AS upp
            ON bom.parent_part_number = upp.part_number
    )
    SELECT 
        upp.part_number, 
        upp.parent_part_number,
        upp.quantity,
        upp.level,
        upp.path,
        p.name,
        p.measure_unit,
        p.status
    FROM under_parent_part_number AS upp
    JOIN part p ON upp.part_number = p.part_number
    ORDER BY upp.path
    ''',
    (part_number, part_number)
    ).fetchall()

    return child_parts

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
            'INSERT into part (part_number, name, measure_unit, owner_id, status)'
            ' VALUES (?,?,?,?,?)',
            (part_number, name, measure_unit, g.user['id'],"creation")
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
        last_modified = datetime.now()
    
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