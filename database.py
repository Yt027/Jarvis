import sqlite3

class Database:
    def __init__(self, path='database/database.db'):
        self.conn = None
        self.path = path
        self.build()

    def save_message(self, role, msg):
        request = f"INSERT INTO messages (role, content) VALUES ({role}, {msg})"
        self.execute(request)

    def build(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row

    def execute(self, request, params=()):
        self.build()
        try:
            cursor = self.conn.execute(request, params)
            self.conn.commit()
            return cursor
        except sqlite3.Error:
            self.conn.rollback()

    def fetchall(self, request, params=()):
        self.build()
        return self.conn.execute(request, params).fetchall()


if __name__ == '__main__':
    database = Database()
    while True:
        cmd = input('/exit pour quitter\n database > ').strip()

        if '/exit' in cmd:
            break

        if not cmd:
            continue

        if cmd.startswith('/fetch '):
            sql = cmd[len('/fetch '):]
            response = database.fetchall(sql)

        else:
            response = database.execute(cmd)


        if response is None:
            print('None')
        elif isinstance(response, list):
            print([dict(row) for row in response])
        else:
            print(dict(response))