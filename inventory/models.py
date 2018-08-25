from users.database import Database, SqliteTable

class Item(SqliteTable):
    """
        The basic inventory item
    """
    
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'item'
        self.order_by_col = 'name'
        self.defaults = {'uom':"Each",}
        
    def create_table(self):
        """Define and create the table"""

        sql = """
            name TEXT,
            description TEXT,
            min_stock NUMBER,
            uom TEXT,
            cat_id INT
            """
        super().create_table(sql)


class Category(SqliteTable):
    """
        Items may be orginaized by category
    """

    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'category'
        self.order_by_col = 'name'
        self.defaults = {}

    def create_table(self):
        """Define and create the table"""

        sql = """
            name TEXT
            """
        super().create_table(sql)

class Transaction(SqliteTable):
    """
        Record as products are added or removed from inventory
    """

    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'transaction'
        self.order_by_col = 'created'
        self.defaults = {}

    def create_table(self):
        """Define and create the table"""

        sql = """
            created DATETIME,
            qty NUMBER, -- May be negative
            value NUMBER, -- per uom
            note TEXT,
            item_id INT,
            FOREIGN KEY (item_id) REFERENCES item(id) ON DELETE CASCADE
            """
        super().create_table(sql)
        
        
class Uom(SqliteTable):
    """
        Unit of Measure look up table
    """

    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'uom'
        self.order_by_col = 'name'
        self.defaults = {}

    def create_table(self):
        """Define and create the table"""

        sql = """
            name TEXT
            """
        super().create_table(sql)
        
    def init_table(self):
        """Create the table and initialize data"""
        self.create_table()
    
        #Try to get a value from the table and create records if none
        rec = self.db.execute('select * from {}'.format(self.table_name)).fetchone()
        if not rec:
            units = [
                ('Each',),
                ('Foot',),
                ('Meter',),
                ('Pair',),
            ]
            self.db.executemany("insert into {} values (null, ?)".format(self.table_name),units)
            self.db.commit()
        

def init_tables(db):
    Item(db).init_table()
    Category(db).init_table()
    Item(db).init_table()
    Uom(db).init_table()