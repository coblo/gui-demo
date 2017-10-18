import peewee as p

from datetime import datetime

from app.backend.rpc import client
from config import db_path

database = p.SqliteDatabase(db_path)


class BaseModel(p.Model):

    class Meta:
        database = database


class Address(BaseModel):

    address = p.CharField(primary_key=True)

    def blocks_mined(self):
        return self.mined_blocks.count()


class Block(BaseModel):

    confirmations = p.IntegerField()
    hash = p.CharField(primary_key=True)
    height = p.IntegerField()
    miner = p.ForeignKeyField(Address, related_name='mined_blocks')
    time = p.DateTimeField()
    txcount = p.IntegerField()

    @staticmethod
    def sync():
        """Synch block data from node"""
        node_height = client.getblockcount()['result']
        latest_block = Block.select().order_by(Block.height.desc()).first()
        latest_block = 1 if latest_block is None else latest_block.height
        if node_height == latest_block:
            return
        else:
            new_blocks = client.listblocks("{}-{}".format(latest_block, node_height))
            synched = 0
            for block in new_blocks['result']:
                addr_obj, adr_created = Address.get_or_create(address=block['miner'])

                block_obj, blk_created = Block.get_or_create(
                    hash=block['hash'],
                    defaults=dict(
                        confirmations=block['confirmations'],
                        miner=addr_obj,
                        height=block['height'],
                        time=datetime.fromtimestamp(block['time']),
                        txcount=block['txcount'],
                    )
                )
                if blk_created:
                    synched += 1
                print('Synced block {}'.format(block_obj.height))

            print('Synced {} blocks total.'.format(synched))


database.connect()
try:
    database.create_tables([Address, Block])
except p.OperationalError as e:
    pass

if __name__ == '__main__':
    Block.sync()
    addr_obj = Address.select().first()
    print(addr_obj.blocks_mined())
    blk_obj = Block.select().first()
    print(blk_obj.time)

