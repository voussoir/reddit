import sqlite3


sql = sqlite3.connect('sql.db')
cur = sql.cursor()

def countTable(table):
    cur.execute("SELECT * FROM '%s'" % table)
    count = 0
    while True:
        row = cur.fetchone()
        if row == None:
            break
        count += 1
    print(table + ': ' + str(count))
    return count

print(str(countTable('complete')))
sql.commit()
