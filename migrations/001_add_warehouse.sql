.bail on

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

.bail off