"""Short demonstration protobuf based SmartLicense"""
import datetime
from smartlicense import smartlicense_pb2 as sl
from google.protobuf import json_format

# Create a SmartLicense object and set Properties
lic = sl.SmartLicense()
lic.licensors.append('wallet-id1')
lic.materials.extend(['iscc1', 'iscc2'])
lic.description = "This License gives you 2 for one!"
lic.rights_profile.extend([sl.ADAPT, sl.LEND, sl.ATTRIBUTION])
lic.activation_modes.append(sl.ON_CHAIN_PAYMENT)
lic.on_chain_price = 5.50
lic.payment_address = 'wallet-id1'
lic.duration.FromTimedelta(datetime.timedelta(days=356))
lic.start_time.FromDatetime(datetime.datetime.now())
lic.territories.append('DE')
lic.access_url = 'https://demo.com'

print('SmartLicense Protobuff Object:')
print('##############################')
print(lic)
print('##############################\n\n')

# Pack object to bytes message:
data_bytes = lic.SerializeToString(deterministic=True)
print('SmartLicense byte serialized for blockchain storage:')
print('##############################')
print('Payload size:', lic.ByteSize(), 'Bytes')
print(data_bytes.hex())
print('##############################\n\n')

# Pack object to json message:
json_string = json_format.MessageToJson(lic, preserving_proto_field_name=True)
print('SmartLicense json serialized:')
print('##############################')
print('Payload size:', len(json_string.encode('utf-8')), 'Bytes')
print(json_string)
print('##############################\n\n')

# Unpack from byte message:
obj1 = sl.SmartLicense()
obj1.ParseFromString(data_bytes)
print('Recovered from bytes:')
print('##############################')
print(obj1)
print('##############################\n\n')


# Unpack from json string
obj2 = json_format.Parse(json_string, sl.SmartLicense())
print('Recovered from json string:')
print('##############################')
print(obj2)
print('##############################\n\n')
