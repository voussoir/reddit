import sys
import sqlite3

master_database = sys.argv[1]
input_database = sys.argv[2]

sql_master = sqlite3.connect(master_database)
cur_master = sql_master.cursor()

sql_input = sqlite3.connect(input_database)
cur_input = sql_input.cursor()

def transfer_table(table, column_count):
    cur_input.execute('SELECT * FROM %s' % table)
    column_string = ', '.join(['?'] * column_count)
    items_moved = 0
    while True:
        fetch = cur_input.fetchone()
        if fetch is None:
            break
        idstr = fetch[1]
        cur_master.execute('SELECT idstr FROM %s WHERE idstr == ?' % table, [idstr])
        if not cur_master.fetchone():
            cur_master.execute('INSERT INTO %s VALUES(%s)' % (table, column_string), fetch)
            items_moved += 1
        if items_moved % 2048 == 1:
            print('.', end='', flush=True)
    print()
    print('moved %d items' % items_moved)
    sql_master.commit()

print('Moving submissions')
transfer_table('submissions', 18)
print('Moving comments')
transfer_table('comments', 11)