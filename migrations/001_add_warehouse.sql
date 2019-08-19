.bail on

CREATE TABLE IF NOT EXISTS 'warehouse' (
            'id' INTEGER NOT NULL PRIMARY KEY,
            name TEXT);
            
insert into warehouse (name) values ("New Warehouse");

-- do this so insert from select will work (match columns)
alter table trx add column warehouse_id INT;
alter table trx add column trx_type TEXT;

CREATE TABLE IF NOT EXISTS 'trx_new' (
            'id' INTEGER NOT NULL PRIMARY KEY,
            created DATETIME,
            qty NUMBER, -- May be negative
            value NUMBER, -- per uom
            note TEXT,
            item_id INT, 
            warehouse_id INT,
            trx_type TEXT, -- Add, Remove, Transfer
            FOREIGN KEY (item_id) REFERENCES item(id) ON DELETE CASCADE,
            FOREIGN KEY (warehouse_id) REFERENCES warehouse(id) ON DELETE CASCADE
            );
            
insert into 'trx_new' select * from trx;
drop table trx;
alter table trx_new rename to trx;
update trx set trx_type = 'Add' where trx.qty > 0;
update trx set trx_type = 'Remove' where trx.qty < 0;
update trx set warehouse_id = 1;
    

.bail off