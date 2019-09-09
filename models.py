from shotglass2.takeabeltof.database import Database, SqliteTable
from shotglass2.takeabeltof.utils import cleanRecordID
from shotglass2.takeabeltof.date_utils import local_datetime_now
from datetime import timedelta

class Item(SqliteTable):
    """
        The basic inventory item
    """
    
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'item'
        self.order_by_col = 'lower(name)'
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


    def _get_warehouse_where(self,**kwargs):
        """Return a snippet of sql to filter by warehouse_id"""

        warehouse_id = cleanRecordID(kwargs.get('warehouse_id'))
        warehouse_where = ''
        if warehouse_id > 0:
            warehouse_where = " and trx.warehouse_id = {} ".format(warehouse_id)
            
        return warehouse_where
        
    def stock_on_hand(self,id,end_date=None,**kwargs):
        
        #import pdb;pdb.set_trace()
        warehouse_where = self._get_warehouse_where(**kwargs)
            
        id = cleanRecordID(id)
        if end_date is None:
            end_date = local_datetime_now()
            
        sql = """select COALESCE(sum(qty), 0) as qty 
                from trx where item_id = {}
                and date(created) <= date("{}") {}
                """.format(id,end_date,warehouse_where)
                
        rec = self.db.execute(sql).fetchone()
        return self.handle_rec_value(rec,'qty')
        
    def additions(self,id,start_date=None,end_date=None,**kwargs):
        
        warehouse_where = self._get_warehouse_where(**kwargs)
        
        id = cleanRecordID(id)
        #import pdb;pdb.set_trace()
        start_date,end_date = self.set_dates(start_date,end_date)
        sql = """select COALESCE(sum(qty), 0) as qty from trx where item_id = {} and qty > 0 
        and date(created) >= date("{}") and date(created) <= date("{}") {}
        """.format(id,start_date,end_date,warehouse_where)
        
        rec = self.db.execute(sql).fetchone()
        return self.handle_rec_value(rec,'qty')
        
    def subtractions(self,id,start_date=None,end_date=None,**kwargs):
            
        warehouse_where = self._get_warehouse_where(**kwargs)
            
        id = cleanRecordID(id)
        start_date,end_date = self.set_dates(start_date,end_date)
        sql = """
            select COALESCE(sum(qty), 0) as qty from trx where item_id = {} and qty < 0
            and date(created) >= date("{}") and date(created) <= date("{}") {}
        """.format(id,start_date,end_date,warehouse_where)
        rec = self.db.execute(sql).fetchone()
        return self.handle_rec_value(rec,'qty')
        
    def lifo_cost(self,id,start_date=None,end_date=None,**kwargs):
        id = cleanRecordID(id)
        start_date,end_date = self.set_dates(start_date,end_date)
        sql = """
            select COALESCE(value, 0) as value from trx where item_id = {} and qty > 0 and value > 0 
            and date(created) >= date("{}") and date(created) <= date("{}")
            order by created desc
        """.format(id,start_date,end_date)
        rec = self.db.execute(sql).fetchone()
        return self.handle_rec_value(rec,'value')
            
    def handle_rec_value(self,rec,elem):
        """Handle the case where no record was found in the calls above"""
        if rec and elem in rec.keys():
            return rec[elem]
        else:
            return 0
        
    def set_dates(self,start_date,end_date):
        """Set the start and end dates if none provided"""
        if start_date is None:
            start_date = local_datetime_now() - timedelta(days=365 * 18) # a long time ago
        if end_date is None:
            end_date = local_datetime_now() + timedelta(days=365) #Next year
    
        return start_date, end_date
            
class Category(SqliteTable):
    """
        Items may be orginaized by category
    """

    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'category'
        self.order_by_col = 'lower(name)'
        self.defaults = {}

    def create_table(self):
        """Define and create the table"""

        sql = """
            name TEXT
            """
        super().create_table(sql)
        
    def category_name(self,id):
        id = cleanRecordID(id)
        rec = self.get(id)
        if rec:
            return rec.name
        else:
            return "Unknown"

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
            warehouse_id INT,
            trx_type TEXT, -- Add, Remove, Transfer
            FOREIGN KEY (item_id) REFERENCES item(id) ON DELETE CASCADE
            FOREIGN KEY (warehouse_id) REFERENCES warehouse(id) ON DELETE CASCADE
            """
        super().create_table(sql)
        
class Transfer(SqliteTable):
    """
        Record item transfers from one warehouse to another
    """

    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'transfer'
        self.order_by_col = 'transfer_date DESC'
        self.defaults = {}

    def create_table(self):
        """Define and create the table"""

        sql = """
            transfer_date DATETIME,
            item_id INT,
            warehouse_out_id INT,
            warehouse_in_id INT,
            -- will want to add a trigger here to reverse transfer_item records prior to delete
            FOREIGN KEY (item_id) REFERENCES item(id) ON DELETE RESTRICT
            """
        super().create_table(sql)
        
class TransferItem(SqliteTable):
    """
        Record how many of item is transfered.
    """

    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'transfer_item'
        self.order_by_col = 'id'
        self.defaults = {}

    def create_table(self):
        """Define and create the table"""

        sql = """
            transfer_id,
            trx_id INT,
            transfer_qty NUMBER, -- May be negative
            FOREIGN KEY (trx_id) REFERENCES trx(id) ON DELETE RESTRICT
            FOREIGN KEY (transfer_id) REFERENCES transfer(id) ON DELETE RESTRICT
            """
        super().create_table(sql)


class Uom(SqliteTable):
    """
        Unit of Measure look up table
    """

    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'uom'
        self.order_by_col = 'lower(name)'
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
            
            
class Warehouse(SqliteTable):
    """
        Places where stuff is stored
    """

    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'warehouse'
        self.order_by_col = 'lower(name)'
        self.defaults = {}

    def create_table(self):
        """Define and create the table"""

        sql = """
            name TEXT,
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
    Warehouse(db).init_table()
    Transfer(db).init_table()
    TransferItem(db).init_table()
    
    