from users.database import Database, SqliteTable

class Item(SqliteTable):
    """
        The basic inventory item
    """
    
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'item'
        self.order_by_col = 'name'
        self.defaults = {'uom':"Ea.","min_stock":3}
        
    def create_table(self):
        """Define and create the table"""

        sql = """
            name TEXT,
            description TEXT,
            min_stock NUMBER DEFAULT 3,
            uom TEXT,
            cat_id INT
            """
        super().create_table(sql)

    def stock_on_hand(self,id):
        on_hand = 0
        if id and id > 0:
            trxs = Transaction(self.db).select(where='item_id = {}'.format(id))
            if trxs:
                for trx in trxs:
                    on_hand += trx.qty
        return on_hand

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
        self.table_name = 'trx'
        self.order_by_col = 'created desc'
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
            

def init_tables(db):
    Item(db).init_table()
    Category(db).init_table()
    Item(db).init_table()
    Uom(db).init_table()
    Transaction(db).init_table()