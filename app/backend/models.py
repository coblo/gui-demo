import logging
import peewee as p
from datetime import datetime
from app import PROFILE_DB, DATA_DB
from app.backend.rpc import client


log = logging.getLogger(__name__)


class Profile(p.Model):
    """Application profile to mangage different Nodes/Accounts"""

    name = p.CharField(primary_key=True)
    chain = p.CharField(default='')
    host = p.CharField(default='')
    port = p.SmallIntegerField(null=True)
    username = p.CharField(default='')
    password = p.CharField(default='')
    use_ssl = p.BooleanField(default=False)
    manage_node = p.BooleanField(default=False)
    active = p.BooleanField(default=False)

    class Meta:
        database = PROFILE_DB

    @staticmethod
    def get_active():
        """Return currently active Pofile"""
        return Profile.select().where(Profile.active).first()


class BaseModel(p.Model):

    class Meta:
        database = DATA_DB


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
        with DATA_DB.atomic():
            for entry in aliases:
                addr = entry['first']['publishers'][0]
                alias = entry['key']
                addr_obj, created = Address.get_or_create(address=addr, defaults=(dict(alias=alias)))
                if not created:
                    addr_obj.alias = alias
                    addr_obj.save()
        log.debug('Synced {} aliases'.format(len(aliases)))


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
            with DATA_DB.atomic():
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
                    log.debug('Synced block {}'.format(block_obj.height))

            log.debug('Synced {} blocks total.'.format(synched))


class VotingRound(BaseModel):

    GRANT, REVOKE, SCOPED_GRANT = 0, 1, 2
    VOTE_TYPES = (
        (GRANT, 'Grant'),
        (REVOKE, 'Revoke'),
        (SCOPED_GRANT, 'Scoped Grant'),
    )

    address = p.ForeignKeyField(Address)
    perm_type = p.CharField(choices=Address.PERMS)
    start_block = p.IntegerField()
    end_block = p.IntegerField()

    vote_type = p.SmallIntegerField(choices=VOTE_TYPES, null=True)
    votes = p.IntegerField(null=True)
    required = p.IntegerField(null=True)

    class Meta:
        primary_key = p.CompositeKey('address', 'perm_type', 'start_block', 'end_block')

    def set_vote_type(self):
        if self.start_block == self.end_block == 0:
            self.vote_type = self.REVOKE
        if self.end_block == 0 and self.end_block == 4294967295:
            self.vote_type = self.GRANT
        else:
            self.vote_type = self.SCOPED_GRANT


def sync_permissions():
    node_height = client.getblockcount()['result']
    permissions = client.listpermissions(','.join(Address.PERMS), verbose=True)['result']

    # Get list of old permissions
    old_permissions = {}
    for address in Address.select():
        address_permissions = []
        for perm in Address.PERMS:
            if getattr(address, 'can_' + perm):
                address_permissions.append(perm)
        if len(address_permissions) > 0:
            old_permissions[address.address] = address_permissions

    # Delete old votes
    VotingRound.delete()

    # Import new permissions
    with DATA_DB.atomic():
        for perm in permissions:
            addr_obj, created = Address.get_or_create(address=perm['address'])
            address = perm['address']
            perm_type = perm['type']
            grant = perm['startblock'] <= node_height <= perm['endblock']
            if address in old_permissions and perm_type in old_permissions[address]:
                old_permissions[address].remove(perm_type)
            setattr(addr_obj, 'can_' + perm_type, grant)
            addr_obj.save()

            for vote_round in perm['pending']:
                vote_obj, created = VotingRound.get_or_create(
                    address=address,
                    perm_type=perm_type,
                    start_block=vote_round['startblock'],
                    end_block=vote_round['endblock'],
                )
                vote_obj.set_vote_type()
                vote_obj.votes = len(vote_round['admins'])
                vote_obj.required = vote_round['required']
                vote_obj.save()

        # Clear all old permissions, that don't exist anymore
        for perm in old_permissions:
            for perm_type in perm:
                setattr(addr_obj, 'can_' + perm_type, False)
                addr_obj.save()

    log.debug('Synced {} permissions'.format(len(permissions)))


PROFILE_DB.create_tables([Profile], True)
DATA_DB.create_tables([Address, Block, VotingRound], True)

if __name__ == '__main__':
    Block.sync()
    Address.sync_aliases()
    sync_permissions()
