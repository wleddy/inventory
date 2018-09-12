from users.database import Database, SqliteTable
from users.utils import cleanRecordID

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

    def _select_sql(self,**kwargs):
        """Return the sql text that will be used by select or select_one
        optional kwargs are:
            where: text to use in the where clause
            order_by: text to include in the order by clause
        
            This version deals with the category.name, item.name sorting that I 
            want to do most of the time
            
            provide a where or order_by kwarg to use standard method instead
            
        """
        where = kwargs.get('where',None)
        order_by = kwargs.get('order_by',None)
        if order_by == None and where == None:
            # do the related order by
            sql = 'SELECT item.* FROM {} '.format(self.table_name)
            sql += 'JOIN category on item.cat_id = category.id '
            sql += 'ORDER BY category.name, item.name'
            return sql
        # else do a normal select
        return super()._select_sql(**kwargs)

    def stock_on_hand(self,id):
        id = cleanRecordID(id)
        return self.db.execute('select sum(qty) as qty from trx where item_id = {}'.format(id)).fetchone()['qty']
        
        

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