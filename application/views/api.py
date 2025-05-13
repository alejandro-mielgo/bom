from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from .part_utils import get_part_list

from .db import get_db

def rows_to_json(rows)->list[dict]:
    return [dict(row) for row in rows]

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/raw_bom',methods=('GET',))
def api_raw_bom():
    db=get_db()
    bom = db.execute("SELECT * FROM bom").fetchall()
    return rows_to_json(bom)


@bp.route('/parts',methods=('GET',))
def api_parts():
    db=get_db()
    parts = db.execute('SELECT * FROM part').fetchall()
    return rows_to_json(parts)

@bp.route('/part_list',methods=('GET',))
def api_part_list():
    part_list = get_part_list()
    return part_list