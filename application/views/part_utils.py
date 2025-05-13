from datetime import datetime
from .db import get_db


"""This file contains the functions to get data from the database """

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
        'SELECT * FROM part JOIN userinfo ON part.owner=userinfo.username'
        ' WHERE part_number=?',(part_number,)
    ).fetchone()
    print(part)
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

    for child in child_parts:
        print(dict(child))

    return child_parts

def update_quantity(child_part:str,parent_part:str,quantity):
    db=get_db()
    db.execute('UPDATE bom'
               ' SET quantity=?'
               ' WHERE part_number=? AND parent_part_number=?',
                (quantity,child_part,parent_part)
                )
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute('UPDATE part SET last_modified=? WHERE part_number=?',(now,parent_part))
    db.commit()


def get_part_list()->list[str]:
    db=get_db()
    parts = db.execute(
        'SELECT * FROM part'
    ).fetchall()

    return [part['part_number'] for part in parts]


