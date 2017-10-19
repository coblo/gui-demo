import peewee as p

from datetime import datetime

from app.backend.rpc import client
from config import db_path

database = p.SqliteDatabase(db_path)


class BaseModel(p.Model):

    class Meta:
        database = database


class Address(BaseModel):

    ISSUE, CREATE, MINE, ADMIN = 'issue', 'create', 'mine', 'admin'
    PERMS = ISSUE, CREATE, MINE, ADMIN

    alias = p.CharField(default='')
    address = p.CharField(primary_key=True)
    can_create = p.BooleanField(default=False)
    can_issue = p.BooleanField(default=False)
    can_mine = p.BooleanField(default=False)
    can_admin = p.BooleanField(default=False)

    def blocks_mined(self):
        return self.mined_blocks.count()

    @classmethod
    def sync_aliases(cls):
        aliases = client.liststreamkeys('alias', verbose=True)['result']
        with database.atomic():
            for entry in aliases:
                addr = entry['first']['publishers'][0]
                alias = entry['key']
                addr_obj, created = Address.get_or_create(address=addr, defaults=(dict(alias=alias)))
                if not created:
                    addr_obj.alias = alias
                    addr_obj.save()
        print('Synced {} aliases'.format(len(aliases)))


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
            with database.atomic():
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

def sync_permissions():
    node_height = client.getblockcount()['result']
    permissions = client.listpermissions(','.join(Address.PERMS))['result']
    addresses = Address.select()

    # Get list of old permissions
    old_permissions = {}
    for address in addresses:
        address_permissions = []
        for perm in Address.PERMS:
            if getattr(address, 'can_' + perm):
                address_permissions.append(perm)
        if len(address_permissions) > 0:
            old_permissions[address.address] = address_permissions

    # Import new permissions
    with database.atomic():
        for perm in permissions:
            addr_obj, created = Address.get_or_create(address=perm['address'])
            address = perm['address']
            perm_type = perm['type']
            grant = perm['endblock'] >= node_height >= perm['startblock']
            if address in old_permissions and perm_type in old_permissions[address]:
                old_permissions[address].remove(perm_type)
            setattr(addr_obj, 'can_' + perm_type, grant)
            addr_obj.save()

        # Clear all old permissions, that don't exist anymore
        for perm in old_permissions:
            for perm_type in perm:
                setattr(addr_obj, 'can_' + perm_type, False)
                addr_obj.save()

    print('Synced {} permissions'.format(len(permissions)))


if __name__ == '__main__':
    Block.sync()
    addr_obj = Address.select().first()
    print(addr_obj.blocks_mined())
    blk_obj = Block.select().first()
    print(blk_obj.time)
    sync_permissions()
    Address.sync_aliases()

