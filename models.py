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
        
        
    def select(self,where=None,order_by=None,**kwargs):
        where = where if where else '1'
        order_by = order_by if order_by else self.order_by_col
        limit = kwargs.get('limit',99999)
        offset = kwargs.get('offset',1)

        sql = """SELECT 
                    item.*, 
                    cats.name as category,
                    COALESCE (
                        (select trx.value from trx 
                            where trx.item_id = item.id  
                            and trx.value > 0 order by trx.created desc limit 1
                        )
                    ,0) as lifo_cost,
                    COALESCE (
                        (select sum(trx.qty) from trx 
                            where trx.item_id = item.id  
                        )
                    ,0) as soh
            
                    from item
                    left join trx on trx.item_id = item.id
                    left join warehouse as wares on wares.id = trx.warehouse_id
                    left join category as cats on cats.id = item.cat_id
            
                    where {where} 
                    group by item.id
                    order by lower(category), lower(item.name)
                    limit {limit}
                    offset {offset}
            """.format(
                where=where,
                limit=limit,
                offset=offset,
                )
        return self.query(sql)


    def _get_warehouse_where(self,**kwargs):
        """Return a snippet of sql to filter by warehouse_id"""

        warehouse_id = cleanRecordID(kwargs.get('warehouse_id'))
        warehouse_where = ''
        if warehouse_id > 0:
            warehouse_where = " and trx.warehouse_id = {} ".format(warehouse_id)
            
        return warehouse_where
        
    def stock_on_hand(self,id,end_date=None,**kwargs):
        """Return the quantity in inventory
        Optional date range may be porvided.
        
        if "warehouse_id" is in kwargs, limit search to that warehouse
        
        """
        
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
        """Return the quantity of of product added to inventory
        Optional date range may be porvided.
        
        if "warehouse_id" is in kwargs, limit search to that warehouse
        
        """
        # 12/13/19 - exclude Transfer transactions
        # 11/13/20 - don't worry about transfers, include all trx.qty > 0
        
        warehouse_where = self._get_warehouse_where(**kwargs)
        
        id = cleanRecordID(id)
        #import pdb;pdb.set_trace()
        start_date,end_date = self.set_dates(start_date,end_date)
        sql = """select COALESCE(sum(qty), 0) as qty from trx where item_id = {} and qty > 0 
        and date(created) >= date("{}") and date(created) <= date("{}") 
        and trx.qty > 0
        {}
        """.format(id,start_date,end_date,warehouse_where)
        
        rec = self.db.execute(sql).fetchone()
        return self.handle_rec_value(rec,'qty')
        
    def subtractions(self,id,start_date=None,end_date=None,**kwargs):
        """Return the quantity of of product removed from inventory
        Optional date range may be porvided.
        
        if "warehouse_id" is in kwargs, limit search to that warehouse
        
        """
        # 12/13/19 - exclude Transfer transactions
        
        warehouse_where = self._get_warehouse_where(**kwargs)
            
        id = cleanRecordID(id)
        start_date,end_date = self.set_dates(start_date,end_date)
        sql = """
            select COALESCE(sum(qty), 0) as qty from trx where item_id = {} and qty < 0
            and date(created) >= date("{}") and date(created) <= date("{}") 
            and trx_type not like 'Transfer%'
            {}
        """.format(id,start_date,end_date,warehouse_where)
        rec = self.db.execute(sql).fetchone()
        return self.handle_rec_value(rec,'qty')
        
    def lifo_cost(self,id,start_date=None,end_date=None,**kwargs):
        """Return the LIFO cost for an item
        Optional date range may be porvided.
        
        if "warehouse_id" is in kwargs, limit search to that warehouse
        
        """
        
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
        self.order_by_col = 'transfer_date'
        self.defaults = {}

    def create_table(self):
        """Define and create the table"""

        sql = """
            transfer_date DATETIME,
            qty NUMBER,
            item_id INT,
            out_trx_id INT,
            in_trx_id INT,
            FOREIGN KEY (item_id) REFERENCES item(id) ON DELETE CASCADE
            FOREIGN KEY (out_trx_id) REFERENCES trx(id) ON DELETE CASCADE
            FOREIGN KEY (in_trx_id) REFERENCES trx(id) ON DELETE CASCADE
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
            FOREIGN KEY (trx_id) REFERENCES trx(id) ON DELETE CASCADE
            FOREIGN KEY (transfer_id) REFERENCES transfer(id) ON DELETE CASCADE
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
    #TransferItem(db).init_table()
    
    